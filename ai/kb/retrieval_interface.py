"""
KB Retrieval Interface Module

Provides the single, clean function interface for solution_finder.py:
- retrieve_kb_context()

This is the ONLY function that solution_finder.py calls.
All internal complexity is hidden behind this interface.

Production-ready with:
- Type safety (full type hints)
- Error handling + fallbacks
- Confidence signals (kb_confident, kb_limit_reached)
- Ranking explanations
- Caching support
"""

from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import logging
import numpy as np
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """Single retrieved KB chunk with metadata."""
    chunk_text: str
    similarity_score: float
    rank: int
    metadata: Dict[str, Any]
    ranking_explanation: Optional[str] = None


@dataclass
class RetrievalMetadata:
    """Aggregated retrieval statistics and signals."""
    mean_similarity: float
    max_similarity: float
    min_similarity: float
    chunk_count: int
    retrieval_latency_ms: float
    kb_confident: bool
    kb_limit_reached: bool
    query_embedding_cached: bool = False
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


def retrieve_kb_context(
    query: str,
    keywords: List[str],
    category: str,
    top_k: int = 5,
    score_threshold: float = 0.40,
    kb_confidence_threshold: float = 0.70,
    max_retrieval_attempts: int = 3,
    attempt_number: int = 1,
    use_hybrid_search: bool = True,
) -> Dict:
    """
    Retrieve ranked KB chunks for a customer ticket query.
    
    This is the MAIN ENTRY POINT for the KB pipeline.
    Called by: agents/solution_finder.py
    
    Args:
        query (str): 
            Customer's reformulated question (from Query Analyzer).
            Example: "How do I reset my password after failed login?"
            
        keywords (List[str]): 
            Extracted keywords from ticket.
            Example: ["password", "reset", "login", "access", "failed"]
            
        category (str): 
            Semantic category from classifier.
            Options: "technique", "facturation", "authentification", "feature_request", "autre"
            
        top_k (int): 
            Number of results to return. Default: 5
            
        score_threshold (float): 
            Minimum cosine similarity threshold for inclusion. Default: 0.40
            Range: 0.0 (any match) to 1.0 (exact match only)
            
        kb_confidence_threshold (float): 
            Threshold for kb_confident flag. Default: 0.70
            kb_confident = True if mean_similarity >= kb_confidence_threshold
            
        max_retrieval_attempts (int): 
            Maximum retry attempts if no results. Default: 3
            
        attempt_number (int): 
            Current attempt number (1-indexed). Default: 1
            
        use_hybrid_search (bool): 
            Use hybrid search (semantic + keyword). Default: True
    
    Returns:
        Dict with structure:
        {
            "results": [
                {
                    "chunk_text": str,           # The actual KB content
                    "similarity_score": float,   # 0.0-1.0 cosine similarity
                    "metadata": {
                        "doc_id": str,           # Source document ID
                        "section": str,          # Section within document
                        "source": str,           # File source
                        "rank": int              # Result rank (0-indexed)
                    },
                    "ranking_explanation": str   # Why this ranked Nth
                },
                ...
            ],
            "metadata": {
                "mean_similarity": float,        # Average of all results
                "max_similarity": float,         # Highest similarity
                "min_similarity": float,         # Lowest similarity
                "chunk_count": int,              # Number of results returned
                "retrieval_latency_ms": float,   # Query latency
                "kb_confident": bool,            # Signal: avg >= threshold
                "kb_limit_reached": bool,        # Signal: attempt >= max
                "query_embedding_cached": bool,  # Was embedding cached?
                "timestamp": str,                # ISO timestamp
                "suggested_fallback": Optional[str]  # If confidence low
            }
        }
    
    Key Signals for Orchestrator:
    
    1. kb_confident (bool):
        - True:  Mean similarity >= kb_confidence_threshold (0.70)
        - False: Mean similarity < threshold
        - Usage: If True → can send satisfaction email after response
                 If False → hold email, wait for feedback
    
    2. kb_limit_reached (bool):
        - True:  attempt_number >= max_retrieval_attempts
        - False: More retry attempts available
        - Usage: If True AND escalated → send escalation email
                 If False AND no results → suggest retry
    
    Example Usage (from solution_finder.py):
    
    ```python
    from kb.retrieval_interface import retrieve_kb_context
    
    kb_result = retrieve_kb_context(
        query=ticket.reformulation,
        keywords=ticket.keywords,
        category=ticket.category,
        top_k=5,
        score_threshold=0.40
    )
    
    # Extract for evaluator
    solution_text = kb_result["results"][0]["chunk_text"] if kb_result["results"] else ""
    kb_confident = kb_result["metadata"]["kb_confident"]
    kb_limit_reached = kb_result["metadata"]["kb_limit_reached"]
    mean_similarity = kb_result["metadata"]["mean_similarity"]
    
    # Pass to evaluator with these signals
    evaluation = evaluate(ticket, solution_text, 
                         kb_confident=kb_confident,
                         kb_limit_reached=kb_limit_reached)
    ```
    """
    import time
    start_time = time.time()
    
    try:
        # STEP 1: Validate inputs
        if not query or not query.strip():
            logger.warning("Empty query provided to retrieve_kb_context")
            return _empty_retrieval_result()
        
        if not keywords:
            keywords = []
        
        if category not in ["technique", "facturation", "authentification", "feature_request", "autre"]:
            logger.warning(f"Unknown category: {category}, defaulting to 'autre'")
            category = "autre"
        
        # STEP 2: Generate query embedding
        try:
            from kb.embeddings import generate_embeddings
            query_embedding = generate_embeddings([query], batch_size=1)[0]
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            return _empty_retrieval_result(error=str(e))
        
        # STEP 3: Perform vector search
        try:
            from kb.vector_store import VectorStoreManager
            vs_manager = VectorStoreManager()
            
            # Semantic search
            semantic_results = vs_manager.search(
                query_embedding=query_embedding,
                top_k=top_k,
                threshold=score_threshold,
                category_filter=category if category != "autre" else None
            )
        except Exception as e:
            logger.error(f"Vector store search failed: {e}")
            semantic_results = []
        
        # STEP 4: Hybrid search (optional keyword boosting)
        if use_hybrid_search and keywords:
            try:
                keyword_boost_results = _keyword_boost_search(
                    semantic_results, keywords, boost_factor=0.15
                )
                semantic_results = keyword_boost_results
            except Exception as e:
                logger.warning(f"Keyword boosting failed: {e}, continuing with semantic")
        
        # STEP 5: Calculate confidence metrics
        if semantic_results:
            similarities = [r["similarity_score"] for r in semantic_results]
            mean_sim = float(np.mean(similarities))
            max_sim = float(np.max(similarities))
            min_sim = float(np.min(similarities))
        else:
            mean_sim = 0.0
            max_sim = 0.0
            min_sim = 0.0
        
        # STEP 6: Determine signals
        kb_confident = mean_sim >= kb_confidence_threshold
        kb_limit_reached = attempt_number >= max_retrieval_attempts
        
        # STEP 7: Format results
        formatted_results = []
        for rank, result in enumerate(semantic_results):
            formatted_results.append({
                "chunk_text": result["chunk_text"],
                "similarity_score": result["similarity_score"],
                "metadata": {
                    "doc_id": result.get("doc_id"),
                    "section": result.get("section", "main"),
                    "source": result.get("source", "unknown"),
                    "rank": rank
                },
                "ranking_explanation": _explain_ranking(
                    rank, result["similarity_score"], mean_sim
                )
            })
        
        # STEP 8: Add suggested fallback if confidence low
        suggested_fallback = None
        if not kb_confident and semantic_results:
            suggested_fallback = (
                f"Low confidence ({mean_sim:.1%}). Consider escalating "
                f"or requesting clarification from customer."
            )
        
        # STEP 9: Build response
        latency_ms = (time.time() - start_time) * 1000
        
        metadata = RetrievalMetadata(
            mean_similarity=mean_sim,
            max_similarity=max_sim,
            min_similarity=min_sim,
            chunk_count=len(formatted_results),
            retrieval_latency_ms=latency_ms,
            kb_confident=kb_confident,
            kb_limit_reached=kb_limit_reached,
            query_embedding_cached=False
        )
        
        response = {
            "results": formatted_results,
            "metadata": asdict(metadata)
        }
        
        if suggested_fallback:
            response["metadata"]["suggested_fallback"] = suggested_fallback
        
        logger.info(
            f"KB retrieval: query_len={len(query)}, keywords={len(keywords)}, "
            f"category={category}, results={len(formatted_results)}, "
            f"mean_sim={mean_sim:.3f}, kb_confident={kb_confident}, "
            f"latency={latency_ms:.1f}ms"
        )
        
        return response
        
    except Exception as e:
        logger.exception(f"Unexpected error in retrieve_kb_context: {e}")
        return _empty_retrieval_result(error=str(e))


def _empty_retrieval_result(error: str = None) -> Dict:
    """Return empty result with appropriate signals."""
    metadata = RetrievalMetadata(
        mean_similarity=0.0,
        max_similarity=0.0,
        min_similarity=0.0,
        chunk_count=0,
        retrieval_latency_ms=0.0,
        kb_confident=False,
        kb_limit_reached=False
    )
    
    response = {
        "results": [],
        "metadata": asdict(metadata)
    }
    
    if error:
        response["metadata"]["error"] = error
    
    return response


def _keyword_boost_search(
    semantic_results: List[Dict],
    keywords: List[str],
    boost_factor: float = 0.15
) -> List[Dict]:
    """Boost results that contain keywords."""
    boosted = []
    
    for result in semantic_results:
        chunk_text = result.get("chunk_text", "").lower()
        keyword_matches = sum(1 for kw in keywords if kw.lower() in chunk_text)
        
        if keyword_matches > 0:
            # Boost score by factor * number of matches
            boost = min(boost_factor * keyword_matches, 0.3)  # Cap at 0.3
            result["similarity_score"] = min(1.0, result["similarity_score"] + boost)
        
        boosted.append(result)
    
    # Re-sort by similarity
    boosted.sort(key=lambda x: x["similarity_score"], reverse=True)
    return boosted


def _explain_ranking(rank: int, similarity: float, mean_similarity: float) -> str:
    """Generate human-readable explanation for result ranking."""
    
    if rank == 0:
        return f"Top match (similarity: {similarity:.1%})"
    
    if similarity >= mean_similarity:
        return f"Above average match (similarity: {similarity:.1%}, mean: {mean_similarity:.1%})"
    
    return f"Below average match (similarity: {similarity:.1%}, mean: {mean_similarity:.1%})"
