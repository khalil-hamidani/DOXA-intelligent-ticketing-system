# pipeline/retrieval.py
"""Vector Retrieval Pipeline: Embedding generation + semantic search.

This module handles:
1. Document embedding generation
2. Vector similarity search
3. Similarity threshold filtering
4. Similarity matrix construction
5. Relevance scoring
"""

from typing import List, Dict, Optional
import numpy as np
from models import Ticket
from rag.embeddings import EmbeddingModel, EmbeddingFactory, embed_query
from rag.vector_store import VectorStore, VectorStoreFactory


class VectorRetriever:
    """Vector-based document retrieval using embeddings and similarity search."""
    
    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        embedder: Optional[EmbeddingModel] = None,
        store_type: str = "in_memory",
        embedder_type: str = "sentence_transformers",
        **kwargs
    ):
        """Initialize retriever.
        
        Args:
            vector_store: VectorStore instance (default: create new)
            embedder: EmbeddingModel instance (default: create new)
            store_type: Type of vector store ("in_memory" | "chroma")
            embedder_type: Type of embedder ("sentence_transformers" | "haystack")
            **kwargs: Additional arguments for store/embedder
        """
        self.vector_store = vector_store or VectorStoreFactory.create(store_type=store_type, **kwargs)
        self.embedder = embedder or EmbeddingFactory.create(embedder_type=embedder_type)
    
    def add_documents(
        self,
        documents: List[Dict],
        batch_size: int = 32
    ) -> List[str]:
        """Add documents to vector store.
        
        Args:
            documents: List of dicts with "id", "content", "metadata" keys
            batch_size: Batch size for embedding generation
            
        Returns:
            List of document IDs
        """
        if not documents:
            return []
        
        # Extract content and generate embeddings
        contents = [doc.get("content", "") for doc in documents]
        
        all_ids = []
        for i in range(0, len(contents), batch_size):
            batch_contents = contents[i:i+batch_size]
            batch_docs = documents[i:i+batch_size]
            
            # Embed batch
            embeddings = self.embedder.embed_documents(batch_contents)
            
            # Add to store
            batch_ids = self.vector_store.add_documents(batch_docs, embeddings)
            all_ids.extend(batch_ids)
        
        return all_ids
    
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.0,
        filters: Optional[Dict] = None
    ) -> Dict:
        """Retrieve similar documents for query.
        
        Args:
            query: Query text
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score (0-1)
            filters: Optional metadata filters
            
        Returns:
            {
                "query": str,
                "results": [{id, content, similarity, metadata}],
                "similarity_matrix": [[scores]],  # Cosine similarity matrix
                "avg_similarity": float,
                "retrieval_info": {k: v}
            }
        """
        # Embed query
        query_embedding = embed_query(query, embedder=self.embedder)
        
        # Search vector store
        results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            threshold=similarity_threshold,
            filters=filters
        )
        
        # Build similarity matrix (query vs results)
        similarity_matrix = []
        for result in results:
            similarity_matrix.append([result["similarity"]])
        
        avg_similarity = np.mean([r["similarity"] for r in results]) if results else 0.0
        
        retrieval_info = {
            "total_results": len(results),
            "threshold_applied": similarity_threshold,
            "query_embedding_dim": len(query_embedding),
            "store_size": self.vector_store.size()
        }
        
        return {
            "query": query,
            "results": results,
            "similarity_matrix": similarity_matrix,
            "avg_similarity": float(avg_similarity),
            "retrieval_info": retrieval_info
        }
    
    def retrieve_by_category(
        self,
        query: str,
        category: str,
        top_k: int = 5,
        similarity_threshold: float = 0.0
    ) -> Dict:
        """Retrieve documents filtered by semantic category.
        
        Args:
            query: Query text
            category: Semantic category (technique, facturation, etc.)
            top_k: Number of results
            similarity_threshold: Minimum similarity
            
        Returns:
            Retrieval result dict
        """
        filters = {"category": category} if category else None
        return self.retrieve(
            query=query,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
            filters=filters
        )
    
    def get_similarity_stats(self, results: List[Dict]) -> Dict:
        """Compute statistics on similarity scores.
        
        Args:
            results: List of retrieval results
            
        Returns:
            Stats dict with min, max, mean, std
        """
        if not results:
            return {"min": 0, "max": 0, "mean": 0, "std": 0, "count": 0}
        
        scores = np.array([r["similarity"] for r in results])
        return {
            "min": float(np.min(scores)),
            "max": float(np.max(scores)),
            "mean": float(np.mean(scores)),
            "std": float(np.std(scores)),
            "count": len(scores)
        }


class SimilarityFilter:
    """Configurable similarity filtering."""
    
    def __init__(self, min_threshold: float = 0.3, max_results: int = 10):
        """Initialize filter.
        
        Args:
            min_threshold: Minimum similarity to include
            max_results: Maximum results to return
        """
        self.min_threshold = min_threshold
        self.max_results = max_results
    
    def filter(self, results: List[Dict]) -> List[Dict]:
        """Filter results by similarity threshold and max count.
        
        Args:
            results: List of retrieval results
            
        Returns:
            Filtered results, sorted by similarity (descending)
        """
        # Sort by similarity descending
        sorted_results = sorted(results, key=lambda x: x["similarity"], reverse=True)
        
        # Apply threshold and max count
        filtered = [r for r in sorted_results if r["similarity"] >= self.min_threshold]
        return filtered[:self.max_results]


class ContextualRetriever:
    """Retriever with context awareness and multi-step retrieval."""
    
    def __init__(self, base_retriever: VectorRetriever):
        """Initialize contextual retriever.
        
        Args:
            base_retriever: Base VectorRetriever instance
        """
        self.base_retriever = base_retriever
        self.similarity_filter = SimilarityFilter()
    
    def retrieve_with_context(
        self,
        ticket: Ticket,
        query_plan: Dict
    ) -> Dict:
        """Retrieve documents with context awareness.
        
        Args:
            ticket: Ticket object
            query_plan: Query plan from QueryPlanner
            
        Returns:
            Enriched retrieval result with context
        """
        search_query = query_plan.get("search_query", ticket.subject)
        search_params = query_plan.get("search_params", {})
        
        category = search_params.get("filter_by_category")
        top_k = search_params.get("top_k", 5)
        similarity_threshold = search_params.get("similarity_threshold", 0.4)
        
        # Step 1: Primary retrieval
        if category:
            primary_results = self.base_retriever.retrieve_by_category(
                query=search_query,
                category=category,
                top_k=top_k,
                similarity_threshold=similarity_threshold
            )
        else:
            primary_results = self.base_retriever.retrieve(
                query=search_query,
                top_k=top_k,
                similarity_threshold=similarity_threshold
            )
        
        # Step 2: Filter results
        filtered_results = self.similarity_filter.filter(primary_results["results"])
        
        # Step 3: Augment with context
        augmentation = {
            "ticket_keywords": ticket.keywords or [],
            "ticket_summary": ticket.summary or "",
            "ticket_category": ticket.category or "",
            "relevance_stats": self.base_retriever.get_similarity_stats(filtered_results)
        }
        
        return {
            "query": search_query,
            "results": filtered_results,
            "augmentation": augmentation,
            "retrieval_info": primary_results.get("retrieval_info", {}),
            "semantic_classes": search_params.get("semantic_classes", [])
        }
    
    def multi_step_retrieve(
        self,
        ticket: Ticket,
        query_plan: Dict,
        fallback_enabled: bool = True
    ) -> Dict:
        """Multi-step retrieval with fallback strategy.
        
        Args:
            ticket: Ticket object
            query_plan: Query plan
            fallback_enabled: Enable fallback to broader search
            
    def get_retrieval_explanation(self, retrieval_result: Dict) -> Dict:
        """
        Generate explanation for why documents ranked in a specific order.
        
        Explains:
        - Why top document ranked first (highest similarity, best match)
        - Why each subsequent document ranked lower
        - Gaps in similarity scores (outliers)
        - Confidence in rankings
        
        Args:
            retrieval_result: Result from retrieve() method
            
        Returns:
            {
                "top_result_explanation": str,
                "ranking_explanation": [str, ...],  # Per result explanation
                "ranking_confidence": float,
                "outlier_analysis": str,
                "retrieval_quality": str,  # "excellent"|"good"|"fair"|"poor"
            }
        """
        results = retrieval_result.get("results", [])
        
        if not results:
            return {
                "top_result_explanation": "No results found for query",
                "ranking_explanation": [],
                "ranking_confidence": 0.0,
                "outlier_analysis": "No documents retrieved",
                "retrieval_quality": "poor"
            }
        
        # Analyze similarities
        similarities = [r["similarity"] for r in results]
        import numpy as np
        
        avg_sim = np.mean(similarities)
        std_sim = np.std(similarities) if len(similarities) > 1 else 0.0
        max_sim = similarities[0] if similarities else 0.0
        
        # Top result explanation
        top_result = results[0]
        top_explanation = (
            f"Top result (#{top_result.get('id')}): "
            f"Highest similarity ({top_result['similarity']:.2%}). "
            f"Best semantic match for query based on embedding distance."
        )
        
        # Per-result explanations
        ranking_explanations = []
        for i, result in enumerate(results, 1):
            sim = result["similarity"]
            
            # Calculate rank drop from previous
            rank_drop = ""
            if i > 1 and similarities:
                prev_sim = similarities[i-2]
                drop_pct = ((prev_sim - sim) / prev_sim * 100) if prev_sim > 0 else 0
                rank_drop = f" ({drop_pct:.1f}% drop from previous)"
            
            # Relative position analysis
            position = ""
            if sim >= avg_sim + std_sim:
                position = "HIGH confidence match"
            elif sim >= avg_sim:
                position = "Medium confidence match"
            elif sim >= avg_sim - std_sim:
                position = "Lower confidence match"
            else:
                position = "Outlier (significantly lower similarity)"
            
            explanation = (
                f"#{i} (ID: {result.get('id')}): "
                f"{sim:.2%} similarity{rank_drop}. {position}."
            )
            ranking_explanations.append(explanation)
        
        # Outlier analysis
        outlier_analysis = ""
        if len(similarities) > 1:
            # Check for significant drops
            drops = []
            for i in range(1, len(similarities)):
                drop = similarities[i-1] - similarities[i]
                if drop > std_sim or drop > 0.2:  # Significant drop
                    drops.append((i, drop))
            
            if drops:
                largest_drop = max(drops, key=lambda x: x[1])
                outlier_analysis = (
                    f"Significant similarity drop after rank #{largest_drop[0]} "
                    f"(drop of {largest_drop[1]:.2%}). "
                    f"Results before this point are more reliable."
                )
            else:
                outlier_analysis = "No significant similarity outliers detected. Gradual ranking."
        else:
            outlier_analysis = "Only one result retrieved."
        
        # Determine retrieval quality
        if max_sim >= 0.8 and len(results) >= 3:
            quality = "excellent"
        elif max_sim >= 0.6 and len(results) >= 2:
            quality = "good"
        elif max_sim >= 0.4 or len(results) >= 2:
            quality = "fair"
        else:
            quality = "poor"
        
        # Ranking confidence (how confident we are in the rankings)
        ranking_confidence = min(max_sim, 1.0)  # Higher similarity = higher confidence
        
        return {
            "top_result_explanation": top_explanation,
            "ranking_explanation": ranking_explanations,
            "ranking_confidence": ranking_confidence,
            "outlier_analysis": outlier_analysis,
            "retrieval_quality": quality,
            "avg_similarity": float(avg_sim),
            "similarity_std_dev": float(std_sim),
            "max_similarity": float(max_sim)
        }
    
    def log_retrieval_details(self, retrieval_result: Dict, query: str = None) -> str:
        """
        Generate detailed retrieval log with explanation.
        
        Args:
            retrieval_result: Result from retrieve() or retrieve_by_category()
            query: Original query string (optional)
            
        Returns:
            Formatted log string with retrieval explanation
        """
        query = query or retrieval_result.get("query", "N/A")
        results = retrieval_result.get("results", [])
        
        # Get explanation
        explanation = self.get_retrieval_explanation(retrieval_result)
        
        # Format log
        log_lines = [
            "=" * 80,
            "RETRIEVAL DETAILS LOG",
            "=" * 80,
            f"Query: {query}",
            f"Results Found: {len(results)}",
            f"Retrieval Quality: {explanation['retrieval_quality'].upper()}",
            f"Ranking Confidence: {explanation['ranking_confidence']:.1%}",
            "",
            "TOP RESULT EXPLANATION:",
            f"  {explanation['top_result_explanation']}",
            "",
            "RANKING DETAILS:",
        ]
        
        for exp in explanation['ranking_explanation']:
            log_lines.append(f"  {exp}")
        
        log_lines.extend([
            "",
            "OUTLIER ANALYSIS:",
            f"  {explanation['outlier_analysis']}",
            "",
            "STATISTICS:",
            f"  Average Similarity: {explanation['avg_similarity']:.2%}",
            f"  Similarity Std Dev: {explanation['similarity_std_dev']:.4f}",
            f"  Max Similarity: {explanation['max_similarity']:.2%}",
            "=" * 80,
        ])
        
        return "\n".join(log_lines)


