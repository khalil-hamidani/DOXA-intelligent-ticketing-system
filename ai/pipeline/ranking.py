# pipeline/ranking.py
"""Ranking Pipeline: Document ranking using Haystack rankers and custom scorers.

Supports:
- Haystack AI rankers (BM25, semantic, etc.)
- Custom relevance scoring
- Multi-factor ranking (semantic + keyword + metadata)
- Configurable ranker selection
"""

from typing import List, Dict, Optional, Callable
import numpy as np
from abc import ABC, abstractmethod


class Ranker(ABC):
    """Abstract ranker interface."""
    
    @abstractmethod
    def rank(self, documents: List[Dict], query: str) -> List[Dict]:
        """Rank documents for query.
        
        Args:
            documents: List of document dicts with "id", "content", "similarity" keys
            query: Query text
            
        Returns:
            Ranked documents, sorted by relevance score (descending)
        """
        pass


class SemanticRanker(Ranker):
    """Semantic ranker using embeddings (cosine similarity)."""
    
    def rank(self, documents: List[Dict], query: str) -> List[Dict]:
        """Rank using semantic similarity.
        
        The documents already have similarity scores from retrieval.
        This ranker simply ensures they're properly sorted and normalized.
        """
        # Sort by similarity (already computed during retrieval)
        ranked = sorted(documents, key=lambda x: x.get("similarity", 0), reverse=True)
        
        # Add rank scores
        for i, doc in enumerate(ranked):
            doc["rank_score"] = doc.get("similarity", 0)
            doc["rank"] = i + 1
        
        return ranked


class KeywordRanker(Ranker):
    """Keyword-based ranker (BM25-like heuristic)."""
    
    def __init__(self, query_weight: float = 0.7, keyword_weight: float = 0.3):
        """Initialize keyword ranker.
        
        Args:
            query_weight: Weight for query keyword matches
            keyword_weight: Weight for document keyword matches
        """
        self.query_weight = query_weight
        self.keyword_weight = keyword_weight
    
    def rank(self, documents: List[Dict], query: str) -> List[Dict]:
        """Rank using keyword matching."""
        query_keywords = set(query.lower().split())
        
        for doc in documents:
            content = doc.get("content", "").lower()
            
            # Count keyword matches
            keyword_matches = sum(1 for kw in query_keywords if kw in content)
            keyword_score = keyword_matches / max(1, len(query_keywords))
            
            # Normalize document length (longer docs shouldn't be penalized)
            length_norm = min(1.0, len(content.split()) / 100)
            
            # Combine with semantic similarity if available
            semantic_score = doc.get("similarity", 0.5)
            
            # Combined score
            combined = (
                semantic_score * self.query_weight +
                (keyword_score * length_norm) * self.keyword_weight
            )
            
            doc["keyword_score"] = keyword_score
            doc["rank_score"] = combined
        
        # Sort by rank score
        ranked = sorted(documents, key=lambda x: x.get("rank_score", 0), reverse=True)
        for i, doc in enumerate(ranked):
            doc["rank"] = i + 1
        
        return ranked


class HybridRanker(Ranker):
    """Hybrid ranker combining semantic and keyword scoring."""
    
    def __init__(
        self,
        semantic_weight: float = 0.6,
        keyword_weight: float = 0.2,
        metadata_weight: float = 0.2
    ):
        """Initialize hybrid ranker.
        
        Args:
            semantic_weight: Weight for semantic similarity
            keyword_weight: Weight for keyword matching
            metadata_weight: Weight for metadata relevance
        """
        self.semantic_weight = semantic_weight
        self.keyword_weight = keyword_weight
        self.metadata_weight = metadata_weight
        
        # Ensure weights sum to 1
        total = semantic_weight + keyword_weight + metadata_weight
        self.semantic_weight /= total
        self.keyword_weight /= total
        self.metadata_weight /= total
    
    def rank(self, documents: List[Dict], query: str) -> List[Dict]:
        """Rank using hybrid scoring."""
        query_keywords = set(query.lower().split())
        
        for doc in documents:
            content = doc.get("content", "").lower()
            
            # Semantic score (from embedding similarity)
            semantic_score = doc.get("similarity", 0.5)
            
            # Keyword score
            keyword_matches = sum(1 for kw in query_keywords if kw in content)
            keyword_score = keyword_matches / max(1, len(query_keywords))
            
            # Metadata score (e.g., category match)
            metadata_score = self._compute_metadata_score(doc, query)
            
            # Hybrid score
            hybrid_score = (
                semantic_score * self.semantic_weight +
                keyword_score * self.keyword_weight +
                metadata_score * self.metadata_weight
            )
            
            doc["rank_score"] = hybrid_score
        
        # Sort by rank score
        ranked = sorted(documents, key=lambda x: x.get("rank_score", 0), reverse=True)
        for i, doc in enumerate(ranked):
            doc["rank"] = i + 1
        
        return ranked
    
    def _compute_metadata_score(self, doc: Dict, query: str) -> float:
        """Compute metadata relevance score."""
        metadata = doc.get("metadata", {})
        
        # If document has category that matches query context, boost
        if "category" in metadata:
            # Simple heuristic: if category appears in query, score 1.0
            if metadata["category"].lower() in query.lower():
                return 1.0
        
        return 0.5  # Default neutral score


class MetadataRanker(Ranker):
    """Metadata-based ranker (category, priority, recency, etc.)."""
    
    def __init__(self, metadata_boost_fn: Optional[Callable[[Dict], float]] = None):
        """Initialize metadata ranker.
        
        Args:
            metadata_boost_fn: Optional function to compute metadata boost
        """
        self.metadata_boost_fn = metadata_boost_fn or self._default_boost
    
    def rank(self, documents: List[Dict], query: str) -> List[Dict]:
        """Rank using metadata."""
        for doc in documents:
            semantic_score = doc.get("similarity", 0.5)
            metadata_boost = self.metadata_boost_fn(doc)
            
            doc["rank_score"] = semantic_score * (1 + metadata_boost)
        
        ranked = sorted(documents, key=lambda x: x.get("rank_score", 0), reverse=True)
        for i, doc in enumerate(ranked):
            doc["rank"] = i + 1
        
        return ranked
    
    def _default_boost(self, doc: Dict) -> float:
        """Default metadata boost function."""
        metadata = doc.get("metadata", {})
        boost = 0.0
        
        # Boost recent documents
        if "updated_at" in metadata:
            boost += 0.1
        
        # Boost by category if available
        if "category" in metadata:
            boost += 0.05
        
        return boost


class RankerFactory:
    """Factory for creating rankers."""
    
    @staticmethod
    def create(ranker_type: str = "semantic", **kwargs) -> Ranker:
        """Create a ranker.
        
        Args:
            ranker_type: "semantic" | "keyword" | "hybrid" | "metadata"
            **kwargs: Arguments passed to ranker constructor
            
        Returns:
            Ranker instance
        """
        if ranker_type == "semantic":
            return SemanticRanker()
        elif ranker_type == "keyword":
            return KeywordRanker(**kwargs)
        elif ranker_type == "hybrid":
            return HybridRanker(**kwargs)
        elif ranker_type == "metadata":
            return MetadataRanker(**kwargs)
        else:
            raise ValueError(f"Unknown ranker type: {ranker_type}")


class RankingPipeline:
    """Pipeline for document ranking with pluggable rankers."""
    
    def __init__(self, ranker: Optional[Ranker] = None, ranker_type: str = "hybrid"):
        """Initialize ranking pipeline.
        
        Args:
            ranker: Ranker instance (default: create from ranker_type)
            ranker_type: Type of ranker to create if ranker not provided
        """
        self.ranker = ranker or RankerFactory.create(ranker_type=ranker_type)
    
    def rank(
        self,
        documents: List[Dict],
        query: str,
        max_results: Optional[int] = None
    ) -> Dict:
        """Rank documents for query.
        
        Args:
            documents: List of documents from retrieval
            query: Query text
            max_results: Optional limit on results
            
        Returns:
            {
                "ranked_documents": [...],
                "query": str,
                "ranking_info": {k: v},
                "top_result": {...}
            }
        """
        if not documents:
            return {
                "ranked_documents": [],
                "query": query,
                "ranking_info": {"count": 0, "ranker": self.ranker.__class__.__name__},
                "top_result": None
            }
        
        # Run ranker
        ranked = self.ranker.rank(documents, query)
        
        # Apply max_results limit
        if max_results:
            ranked = ranked[:max_results]
        
        # Compute ranking statistics
        scores = [doc.get("rank_score", 0) for doc in ranked]
        
        return {
            "ranked_documents": ranked,
            "query": query,
            "ranking_info": {
                "count": len(ranked),
                "ranker": self.ranker.__class__.__name__,
                "score_stats": {
                    "min": float(np.min(scores)) if scores else 0,
                    "max": float(np.max(scores)) if scores else 0,
                    "mean": float(np.mean(scores)) if scores else 0,
                    "std": float(np.std(scores)) if scores else 0
                }
            },
            "top_result": ranked[0] if ranked else None
        }
    
    def reconfigure_ranker(self, ranker_type: str, **kwargs):
        """Reconfigure the ranking strategy.
        
        Args:
            ranker_type: Type of ranker
            **kwargs: Arguments for ranker
        """
        self.ranker = RankerFactory.create(ranker_type=ranker_type, **kwargs)
