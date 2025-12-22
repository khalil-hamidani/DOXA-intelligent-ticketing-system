"""
Knowledge Base Retriever Module

Query interface for retrieving documents from KB using Haystack AI + Qdrant.
Provides semantic search with cosine similarity scoring for ticket system integration.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from loguru import logger

from kb.config import KBConfig
from kb.embeddings import HaystackEmbeddingStore


@dataclass
class SearchResult:
    """Represents a search result from KB."""
    chunk_id: str
    content: str
    similarity_score: float  # Cosine similarity (0.0 to 1.0)
    metadata: Dict[str, Any]
    source_file: str
    section_title: Optional[str] = None
    page_number: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "similarity_score": round(self.similarity_score, 3),
            "metadata": self.metadata,
            "source_file": self.source_file,
            "section_title": self.section_title,
            "page_number": self.page_number,
        }


class HaystackRetriever:
    """Haystack AI-based retriever using Qdrant vector database.
    
    Provides semantic search with cosine similarity scoring.
    Designed for ticket system KB context retrieval.
    """
    
    def __init__(
        self,
        kb_manager: KnowledgeBaseManager,
def __init__(
        self,
        config: Optional[KBConfig] = None,
    ):
        """
        Initialize Haystack retriever.
        
        Args:
            config: KBConfig instance (uses default if not provided)
        """
        self.config = config or KBConfig()
        self.embedding_store = HaystackEmbeddingStore(self.config)
        logger.info("Initialized HaystackRetriever with Qdrant backend")
    
    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
    ) -> List[SearchResult]:
        """
        Search for documents matching query using cosine similarity.
        
        Args:
            query: Search query text
            top_k: Number of top results to return (default from config)
            threshold: Minimum cosine similarity threshold (default from config)
        
        Returns:
            List of SearchResult objects sorted by similarity (descending)
        """
        top_k = top_k or self.config.top_k
        threshold = threshold if threshold is not None else self.config.similarity_threshold
        
        logger.info(f"Searching KB for: '{query}' (top_k={top_k}, threshold={threshold})")
        
        # Search using Haystack
        raw_results = self.embedding_store.search(query, top_k=top_k, threshold=threshold)
        
        if not raw_results:
            logger.info("No results found for query")
            return []
        
        # Convert raw results to SearchResult objects
        results = []
        for chunk_id, similarity_score, metadata in raw_results:
            result = SearchResult(
                chunk_id=chunk_id,
                content=metadata.get("content", ""),
                similarity_score=similarity_score,
                metadata=metadata,
                source_file=metadata.get("source_file", ""),
                section_title=metadata.get("section_title"),
                page_number=metadata.get("page_number"),
            )
            results.append(result)
        
        logger.info(f"Found {len(results)} relevant chunks (avg similarity: {sum(r.similarity_score for r in results) / len(results):.3f})")
        return results
    
    def search_by_section(
        self,
        query: str,
        section_title: str,
        top_k: Optional[int] = None,
    ) -> List[SearchResult]:
        """
        Search within a specific document section.
        
        Args:
            query: Search query
            section_title: Filter by section title (e.g., "Installation", "Troubleshooting")
            top_k: Number of results
        
        Returns:
            Results filtered to specified section
        """
        results = self.search(query, top_k=top_k)
        filtered = [
            r for r in results
            if r.section_title and section_title.lower() in r.section_title.lower()
        ]
        logger.info(f"Filtered {len(results)} results to section '{section_title}': {len(filtered)} matches")
        return filtered
    
    def search_by_source(
        self,
        query: str,
        source_file: str,
        top_k: Optional[int] = None,
    ) -> List[SearchResult]:
        """
        Search within a specific document source.
        
        Args:
            query: Search query
            source_file: Filter by source file name
            top_k: Number of results
        
        Returns:
            Results from specified source
        """
        results = self.search(query, top_k=top_k)
        filtered = [
            r for r in results
            if source_file.lower() in r.source_file.lower()
        ]
        logger.info(f"Filtered {len(results)} results to source '{source_file}': {len(filtered)} matches")
        return filtered
    
    def get_context_string(
        self,
        query: str,
        top_k: Optional[int] = None,
        include_metadata: bool = True,
    ) -> str:
        """
        Get search results as formatted context string for embedding in prompts.
        
        Args:
            query: Search query
            top_k: Number of results
            include_metadata: Include source/section metadata in output
        
        Returns:
            Formatted context string ready for LLM prompts
        """
        results = self.search(query, top_k=top_k)
        
        if not results:
            return "No relevant context found in knowledge base."
        
        context_parts = []
        for i, result in enumerate(results, 1):
            lines = []
            if include_metadata:
                lines.append(f"[Source: {result.source_file}]")
                if result.section_title:
                    lines.append(f"[Section: {result.section_title}]")
                lines.append(f"[Relevance: {result.similarity_score:.1%}]")
            lines.append(result.content)
            context_parts.append("\n".join(lines))
        
        return "\n\n---\n\n".join(context_parts)
    
    def get_kb_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        try:
            stats = self.embedding_store.get_stats()
            stats.update({
                "top_k": self.config.top_k,
                "similarity_threshold": self.config.similarity_threshold,
                "chunk_size": self.config.chunk_size,
                "chunk_overlap": self.config.chunk_overlap,
            })
            return stats
        except Exception as e:
            logger.error(f"Error getting KB stats: {e}")
            return {}


class TicketKBInterface:
    """
    Thin wrapper around HaystackRetriever for ticket system integration.
    
    Provides high-level methods for ticket processing with KB context.
    """
    
    def __init__(self, config: Optional[KBConfig] = None):
        """
        Initialize ticket KB interface.
        
        Args:
            config: KBConfig instance
        """
        self.retriever = HaystackRetriever(config)
        self.config = config or self.retriever.config
        logger.info("Initialized TicketKBInterface for ticket processing")
    
    def get_context_for_ticket(
        self,
        ticket_subject: str,
        ticket_description: str,
        top_k: Optional[int] = None,
    ) -> Tuple[str, List[SearchResult]]:
        """
        Get relevant KB context for a ticket.
        
        Args:
            ticket_subject: Ticket subject/title
            ticket_description: Ticket description/problem statement
            top_k: Number of KB results to retrieve
        
        Returns:
            Tuple of (formatted_context_string, detailed_results)
        """
        # Combine subject and description into search query
        query = f"{ticket_subject}. {ticket_description}"
        
        # Retrieve relevant documents
        results = self.retriever.search(query, top_k=top_k)
        
        # Get formatted context string for LLM prompt
        context = self.retriever.get_context_string(query, top_k=top_k)
        
        logger.info(f"Retrieved KB context for ticket (found {len(results)} relevant chunks)")
        return context, results
    
    def get_answer_from_kb(
        self,
        question: str,
        top_k: int = 3,
    ) -> Tuple[Optional[str], float]:
        """
        Get best answer from KB for a question.
        
        Args:
            question: Question to search for
            top_k: Number of chunks to consider
        
        Returns:
            Tuple of (answer_content, confidence_score) or (None, 0.0) if no match
        """
        results = self.retriever.search(question, top_k=top_k)
        
        if results:
            best_result = results[0]
            logger.info(f"Found KB answer with {best_result.similarity_score:.1%} confidence")
            return best_result.content, best_result.similarity_score
        
        logger.info("No answer found in KB for question")
        return None, 0.0
    
    def search_faq(
        self,
        question: str,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search FAQ section for common questions.
        
        Args:
            question: FAQ question
            top_k: Number of FAQ matches
        
        Returns:
            List of FAQ results as dicts
        """
        results = self.retriever.search_by_section(question, "FAQ", top_k=top_k)
        return [r.to_dict() for r in results]
