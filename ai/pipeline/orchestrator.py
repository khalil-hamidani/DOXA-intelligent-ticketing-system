# pipeline/orchestrator.py
"""RAG Pipeline Orchestrator: Integrates all stages from Query Intelligence to Answer Generation.

Provides high-level orchestration for the complete RAG workflow:
1. Query Intelligence (validation, augmentation, classification, planning)
2. Retrieval (embedding-based vector search)
3. Ranking (pluggable rankers)
4. Context Augmentation (optimization, chunking, merging)
5. Answer Generation (LLM-based response)
"""

from typing import Dict, Optional, List
from models import Ticket
from pipeline.query_intelligence import process_query_intelligence, QueryPlanner
from pipeline.retrieval import VectorRetriever, ContextualRetriever
from pipeline.ranking import RankingPipeline, RankerFactory
from pipeline.context import ContextOptimizer, ContextBuilder
from pipeline.answer import ContextAwareAnswerGenerator, ResponseValidator
from rag.embeddings import EmbeddingFactory
from rag.vector_store import VectorStoreFactory
from config.pipeline_config import PipelineConfig, get_pipeline_config


class RAGPipeline:
    """Complete RAG pipeline orchestrator."""
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        """Initialize RAG pipeline.
        
        Args:
            config: PipelineConfig instance (default: from environment)
        """
        self.config = config or get_pipeline_config()
        
        # Initialize components
        self.embedder = EmbeddingFactory.create(
            embedder_type=self.config.embedding.embedder_type,
            model_name=self.config.embedding.model_name
        )
        
        self.vector_store = VectorStoreFactory.create(
            store_type=self.config.vector_store.store_type,
            collection_name=self.config.vector_store.collection_name,
            persist_dir=self.config.vector_store.persist_dir
        )
        
        self.base_retriever = VectorRetriever(
            vector_store=self.vector_store,
            embedder=self.embedder
        )
        
        self.retriever = ContextualRetriever(self.base_retriever)
        
        self.ranker = RankingPipeline(
            ranker_type=self.config.ranker.ranker_type
        )
        
        self.context_optimizer = ContextOptimizer(
            target_tokens=self.config.context.target_tokens,
            prioritize_similarity=self.config.context.prioritize_similarity
        )
        
        self.answer_generator = ContextAwareAnswerGenerator()
        
        self.response_validator = ResponseValidator(
            min_confidence=self.config.answer.min_confidence
        )
    
    def add_documents(self, documents: List[Dict]) -> Dict:
        """Add documents to vector store.
        
        Args:
            documents: List of dicts with "id", "content", "metadata" keys
            
        Returns:
            {
                "added_count": int,
                "document_ids": List[str],
                "status": "success" | "error"
            }
        """
        try:
            added_ids = self.base_retriever.add_documents(documents)
            return {
                "added_count": len(added_ids),
                "document_ids": added_ids,
                "status": "success"
            }
        except Exception as e:
            return {
                "added_count": 0,
                "document_ids": [],
                "status": "error",
                "error": str(e)
            }
    
    def process_ticket(self, ticket: Ticket) -> Dict:
        """Run complete RAG pipeline for a ticket.
        
        Args:
            ticket: Ticket object
            
        Returns:
            Complete pipeline result with all stages
        """
        result = {
            "ticket_id": ticket.id,
            "stages": {}
        }
        
        # Stage 1: Query Intelligence
        qi_result = process_query_intelligence(ticket, augment=True)
        result["stages"]["query_intelligence"] = qi_result
        
        if not qi_result.get("validation", {}).get("valid", False):
            result["status"] = "rejected"
            return result
        
        # Stage 2: Query Planning
        planner = QueryPlanner()
        plan = planner.plan(ticket, qi_result.get("classification", {}))
        result["stages"]["query_plan"] = plan
        
        # Stage 3: Retrieval
        retrieval_result = self.retriever.multi_step_retrieve(
            ticket=ticket,
            query_plan=plan,
            fallback_enabled=True
        )
        result["stages"]["retrieval"] = {
            "retrieved_count": len(retrieval_result.get("results", [])),
            "query": retrieval_result.get("query"),
            "avg_similarity": self._compute_avg_similarity(retrieval_result.get("results", [])),
            "fallback_applied": retrieval_result.get("fallback_applied", False)
        }
        
        # Stage 4: Ranking
        ranking_result = self.ranker.rank(
            documents=retrieval_result.get("results", []),
            query=retrieval_result.get("query", ""),
            max_results=self.config.retriever.max_results
        )
        result["stages"]["ranking"] = {
            "ranked_count": len(ranking_result.get("ranked_documents", [])),
            "ranker": ranking_result.get("ranking_info", {}).get("ranker", "unknown"),
            "top_score": ranking_result.get("top_result", {}).get("rank_score", 0) if ranking_result.get("top_result") else 0
        }
        
        # Stage 5: Context Optimization
        opt_result = self.context_optimizer.optimize(
            documents=ranking_result.get("ranked_documents", []),
            query=retrieval_result.get("query", "")
        )
        result["stages"]["context_optimization"] = {
            "selected_documents": len(opt_result.get("selected_documents", [])),
            "token_estimate": opt_result.get("token_estimate", 0),
            "efficiency": opt_result.get("optimization_info", {}).get("efficiency", 0)
        }
        
        # Stage 6: Answer Generation
        answer_result = self.answer_generator.generate_with_context(
            ticket=ticket,
            context_result=opt_result
        )
        result["stages"]["answer_generation"] = {
            "confidence": answer_result.get("answer_generation", {}).get("confidence", 0),
            "escalation_recommended": answer_result.get("escalation_recommended", False),
            "source": answer_result.get("answer_generation", {}).get("source", "unknown")
        }
        
        # Stage 7: Response Validation
        validation = self.response_validator.validate(answer_result.get("answer_generation", {}))
        result["stages"]["validation"] = {
            "valid": validation.get("valid", False),
            "issues": validation.get("issues", []),
            "recommendations": validation.get("recommendations", [])
        }
        
        # Final response
        result["final_response"] = answer_result.get("final_response", "")
        result["status"] = "answered"
        
        return result
    
    @staticmethod
    def _compute_avg_similarity(documents: List[Dict]) -> float:
        """Compute average similarity score."""
        if not documents:
            return 0.0
        similarities = [doc.get("similarity", 0) for doc in documents]
        return sum(similarities) / len(similarities)
    
    def reconfigure(self, config: PipelineConfig):
        """Reconfigure pipeline with new configuration.
        
        Args:
            config: New PipelineConfig
        """
        self.config = config
        # Note: Component reinitialization would happen on next operation
    
    def get_stats(self) -> Dict:
        """Get pipeline statistics.
        
        Returns:
            Stats dict with store size, embedding dim, etc.
        """
        return {
            "vector_store_size": self.vector_store.size(),
            "embedding_dim": self.embedder.get_embedding_dim(),
            "ranker_type": self.config.ranker.ranker_type,
            "store_type": self.config.vector_store.store_type,
            "embedding_model": self.config.embedding.model_name
        }


class SimplifiedRAGPipeline:
    """Simplified RAG pipeline for basic use cases."""
    
    def __init__(self):
        """Initialize with default configuration."""
        self.pipeline = RAGPipeline(config=PipelineConfig.default())
    
    def add_kb_documents(self, kb_entries: List[Dict]) -> Dict:
        """Add knowledge base entries to vector store.
        
        Args:
            kb_entries: List of KB entries with "id", "category", "content" fields
            
        Returns:
            Result of add_documents
        """
        documents = [
            {
                "id": entry.get("id", f"kb_{i}"),
                "content": entry.get("content", ""),
                "metadata": {
                    "category": entry.get("category", ""),
                    "source": "kb"
                }
            }
            for i, entry in enumerate(kb_entries)
        ]
        return self.pipeline.add_documents(documents)
    
    def answer_ticket(self, ticket: Ticket) -> str:
        """Get answer for a ticket.
        
        Args:
            ticket: Ticket object
            
        Returns:
            Final response string
        """
        result = self.pipeline.process_ticket(ticket)
        return result.get("final_response", "Unable to generate answer.")
