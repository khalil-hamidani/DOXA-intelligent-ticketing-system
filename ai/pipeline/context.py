# pipeline/context.py
"""Context Augmentation: Merging, chunking, and structuring retrieved documents.

This module handles:
1. Document merging and deduplication
2. Chunking strategies for context windows
3. Context window optimization
4. Metadata preservation and enrichment
5. Context structure building for LLM consumption
"""

from typing import List, Dict, Optional, Tuple
from models import Ticket
import re


class DocumentMerger:
    """Merges and deduplicates retrieved documents."""
    
    @staticmethod
    def merge(documents: List[Dict], strategy: str = "concatenate") -> str:
        """Merge document content into single context.
        
        Args:
            documents: List of documents with "content" and "id" fields
            strategy: "concatenate" | "summary" | "structured"
            
        Returns:
            Merged context string
        """
        if not documents:
            return ""
        
        if strategy == "concatenate":
            return DocumentMerger._concatenate(documents)
        elif strategy == "summary":
            return DocumentMerger._summary_merge(documents)
        elif strategy == "structured":
            return DocumentMerger._structured_merge(documents)
        else:
            return DocumentMerger._concatenate(documents)
    
    @staticmethod
    def _concatenate(documents: List[Dict]) -> str:
        """Simple concatenation with separators."""
        parts = []
        for i, doc in enumerate(documents, 1):
            content = doc.get("content", "").strip()
            if content:
                parts.append(f"[Document {i}]\n{content}")
        
        return "\n\n---\n\n".join(parts)
    
    @staticmethod
    def _summary_merge(documents: List[Dict]) -> str:
        """Merge with importance-based selection."""
        # Keep high-ranking documents, summarize lower-ranking
        if len(documents) <= 3:
            return DocumentMerger._concatenate(documents)
        
        # Keep top 3 full, summarize rest
        parts = []
        for i, doc in enumerate(documents[:3], 1):
            content = doc.get("content", "").strip()
            if content:
                parts.append(f"[Document {i}]\n{content}")
        
        # Add summary of remaining
        if len(documents) > 3:
            remaining_ids = [doc.get("id", f"doc_{i}") for i, doc in enumerate(documents[3:], 4)]
            parts.append(f"\n[Additional documents referenced: {', '.join(remaining_ids)}]")
        
        return "\n\n---\n\n".join(parts)
    
    @staticmethod
    def _structured_merge(documents: List[Dict]) -> str:
        """Structured merge with metadata preservation."""
        parts = []
        for i, doc in enumerate(documents, 1):
            content = doc.get("content", "").strip()
            metadata = doc.get("metadata", {})
            similarity = doc.get("similarity", 0)
            
            header = f"[Document {i} | ID: {doc.get('id')} | Relevance: {similarity:.2%}]"
            if metadata.get("category"):
                header += f" | Category: {metadata['category']}"
            
            if content:
                parts.append(f"{header}\n{content}")
        
        return "\n\n---\n\n".join(parts)


class ContextChunker:
    """Chunks documents to fit within context windows."""
    
    def __init__(self, max_tokens: int = 4000, overlap: int = 100):
        """Initialize chunker.
        
        Args:
            max_tokens: Maximum tokens per context window
            overlap: Token overlap between chunks for continuity
        """
        self.max_tokens = max_tokens
        self.overlap = overlap
    
    def chunk(self, context: str) -> List[Dict]:
        """Chunk context into window-sized pieces.
        
        Args:
            context: Full context string
            
        Returns:
            List of chunks with metadata
        """
        # Simple token estimation: ~4 chars per token
        chunk_size = self.max_tokens * 4
        overlap_size = self.overlap * 4
        
        chunks = []
        start = 0
        chunk_num = 1
        
        while start < len(context):
            end = min(start + chunk_size, len(context))
            
            # Try to break at a sentence boundary
            if end < len(context):
                last_period = context.rfind(".", start, end)
                if last_period > start and last_period > start + chunk_size // 2:
                    end = last_period + 1
            
            chunk_text = context[start:end].strip()
            if chunk_text:
                chunks.append({
                    "chunk_id": chunk_num,
                    "content": chunk_text,
                    "start_pos": start,
                    "end_pos": end,
                    "token_estimate": len(chunk_text) // 4
                })
                chunk_num += 1
            
            # Move start position (with overlap)
            start = end - overlap_size if end < len(context) else len(context)
        
        return chunks if chunks else [{"chunk_id": 1, "content": context, "token_estimate": len(context) // 4}]


class ContextOptimizer:
    """Optimizes context for LLM consumption."""
    
    def __init__(self, target_tokens: int = 2000, prioritize_similarity: bool = True):
        """Initialize optimizer.
        
        Args:
            target_tokens: Target context size in tokens
            prioritize_similarity: If True, prioritize high-similarity docs
        """
        self.target_tokens = target_tokens
        self.prioritize_similarity = prioritize_similarity
    
    def optimize(self, documents: List[Dict], query: str) -> Dict:
        """Optimize document selection for context window.
        
        Args:
            documents: Ranked documents from retrieval + ranking
            query: Original query
            
        Returns:
            {
                "selected_documents": [...],
                "context": str,
                "token_estimate": int,
                "optimization_info": {k: v}
            }
        """
        if not documents:
            return {
                "selected_documents": [],
                "context": "",
                "token_estimate": 0,
                "optimization_info": {"reason": "No documents provided"}
            }
        
        # Select documents to fit in context window
        selected = []
        total_tokens = 0
        query_tokens = len(query.split()) * 1.5  # Estimate with overhead
        available_tokens = self.target_tokens - int(query_tokens)
        
        for doc in documents:
            doc_tokens = doc.get("token_estimate", len(doc.get("content", "")) // 4)
            
            if total_tokens + doc_tokens <= available_tokens:
                selected.append(doc)
                total_tokens += doc_tokens
            elif total_tokens < available_tokens:
                # Truncate last document to fit
                remaining = available_tokens - total_tokens
                truncated_content = self._truncate_to_tokens(
                    doc.get("content", ""),
                    remaining
                )
                if truncated_content:
                    doc_copy = doc.copy()
                    doc_copy["content"] = truncated_content + "..."
                    doc_copy["truncated"] = True
                    selected.append(doc_copy)
                    total_tokens += remaining
                break
        
        # Build context
        merger = DocumentMerger()
        context = merger.merge(selected, strategy="structured")
        
        return {
            "selected_documents": selected,
            "context": context,
            "token_estimate": total_tokens + int(query_tokens),
            "optimization_info": {
                "total_documents": len(documents),
                "selected_documents": len(selected),
                "available_tokens": available_tokens,
                "used_tokens": total_tokens,
                "efficiency": total_tokens / available_tokens if available_tokens > 0 else 0,
                "truncated": any(doc.get("truncated", False) for doc in selected)
            }
        }
    
    @staticmethod
    def _truncate_to_tokens(text: str, max_tokens: int) -> str:
        """Truncate text to approximately max_tokens."""
        char_limit = max_tokens * 4
        if len(text) <= char_limit:
            return text
        
        # Truncate at last sentence
        truncated = text[:char_limit]
        last_period = truncated.rfind(".")
        if last_period > char_limit // 2:
            return truncated[:last_period + 1]
        
        return truncated


class ContextBuilder:
    """Builds structured context for LLM consumption."""
    
    @staticmethod
    def build_prompt_context(
        ticket: Ticket,
        optimization_result: Dict
    ) -> str:
        """Build a formatted prompt with context.
        
        Args:
            ticket: Ticket object
            optimization_result: Result from ContextOptimizer
            
        Returns:
            Formatted prompt string ready for LLM
        """
        context = optimization_result.get("context", "")
        
        prompt = f"""You are a support agent helping with ticket resolution.

TICKET INFORMATION:
- Subject: {ticket.subject}
- Category: {ticket.category or 'unclassified'}
- Priority: {ticket.priority_score or 'N/A'} / 100
- Summary: {ticket.summary or ticket.description}
- Keywords: {', '.join(ticket.keywords or [])}

RETRIEVED CONTEXT:
{context}

TASK:
Based on the retrieved documents and ticket information, provide a comprehensive and contextual solution.
Focus on the most relevant information. If no relevant solution is found, acknowledge the issue and suggest escalation."""
        
        return prompt
    
    @staticmethod
    def build_structured_context(
        ticket: Ticket,
        optimization_result: Dict
    ) -> Dict:
        """Build structured context dict for programmatic consumption.
        
        Args:
            ticket: Ticket object
            optimization_result: Result from ContextOptimizer
            
        Returns:
            Structured context dict
        """
        return {
            "ticket": {
                "id": ticket.id,
                "subject": ticket.subject,
                "category": ticket.category,
                "priority": ticket.priority_score,
                "keywords": ticket.keywords or []
            },
            "retrieved_documents": optimization_result.get("selected_documents", []),
            "context_text": optimization_result.get("context", ""),
            "context_optimization": optimization_result.get("optimization_info", {}),
            "metadata": {
                "total_tokens_estimate": optimization_result.get("token_estimate", 0),
                "context_efficiency": optimization_result.get("optimization_info", {}).get("efficiency", 0)
            }
        }
