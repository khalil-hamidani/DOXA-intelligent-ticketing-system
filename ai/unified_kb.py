"""
Unified Knowledge Base Integration
Provides RAG-based document retrieval for the entire ticketing system.
"""

import os
import json
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Load .env
_base_dir = os.path.dirname(os.path.abspath(__file__))  # ai/
_kb_dir = os.path.join(_base_dir, "kb")  # ai/kb/
load_dotenv(os.path.join(_kb_dir, ".env"))


class UnifiedKnowledgeBase:
    """
    Unified KB that combines:
    1. RAG retrieval from indexed documents (ChromaDB or JSON)
    2. Context building from retrieved chunks
    3. Integration point for orchestrator
    """

    def __init__(self, kb_dir: str = None, use_json: bool = True):
        """
        Initialize the KB.
        
        Args:
            kb_dir: Path to KB directory (default: ai/kb)
            use_json: If True, use JSON retriever (faster, no embeddings)
                     If False, use ChromaDB (slower but semantic)
        """
        if kb_dir is None:
            kb_dir = _kb_dir
        
        self.kb_dir = kb_dir
        self.use_json = use_json
        self.retriever = None
        self.initialized = False
        
        self._init_retriever()
    
    def _init_retriever(self):
        """Initialize the appropriate retriever."""
        import sys
        
        # Add kb directory to path FIRST
        if self.kb_dir not in sys.path:
            sys.path.insert(0, self.kb_dir)
        
        try:
            if self.use_json:
                # Direct import after adding to sys.path
                import simple_retriever
                index_path = os.path.join(self.kb_dir, "index.json")
                if os.path.exists(index_path):
                    self.retriever = simple_retriever.SimpleRetriever(index_path)
                    self.initialized = True
                    return
            
            # Fallback to ChromaDB
            import retriever
            chroma_path = os.path.join(self.kb_dir, "chroma_db")
            if os.path.exists(chroma_path):
                self.retriever = retriever.Retriever()
                self.initialized = True
                return
                
        except ImportError as e:
            print(f"⚠️ Failed to import retriever: {e}")
        except Exception as e:
            print(f"⚠️ Failed to initialize retriever: {e}")
        
        if not self.initialized:
            print(f"⚠️ Knowledge base not initialized at {self.kb_dir}. Please run ingest scripts.")
    
    def retrieve(self, query: str, k: int = 5, threshold: float = 0.1) -> List[Dict]:
        """
        Retrieve relevant documents from KB.
        
        Args:
            query: Question or search query
            k: Number of results
            threshold: Minimum similarity score
        
        Returns:
            List of documents with content, meta, and score
        """
        if not self.initialized or self.retriever is None:
            return []
        
        try:
            return self.retriever.retrieve(query, k=k, threshold=threshold)
        except Exception as e:
            print(f"❌ Retrieval error: {e}")
            return []
    
    def get_context(self, query: str, k: int = 5, max_chars: int = 3000) -> str:
        """
        Get formatted context from KB for a query.
        
        Args:
            query: Question or search query
            k: Number of documents to retrieve
            max_chars: Maximum context size
        
        Returns:
            Formatted context string ready for LLM
        """
        docs = self.retrieve(query, k=k)
        if not docs:
            return ""
        
        context_parts = []
        total_len = 0
        
        for i, doc in enumerate(docs, 1):
            source = doc.get("meta", {}).get("source", "unknown")
            score = doc.get("score", 0)
            content = doc.get("content", "")
            
            block = f"[Résultat {i}]\nSource: {source}\nScore: {score}\n{content}\n"
            
            if total_len + len(block) > max_chars:
                break
            
            context_parts.append(block)
            total_len += len(block)
        
        return "\n---\n".join(context_parts)
    
    def search_and_answer(self, query: str, k: int = 5) -> Dict:
        """
        Search KB and prepare answer context.
        
        Returns:
            {
                "query": original query,
                "documents": list of retrieved docs,
                "context": formatted context string,
                "has_results": bool
            }
        """
        docs = self.retrieve(query, k=k)
        context = self.get_context(query, k=k)
        
        return {
            "query": query,
            "documents": docs,
            "context": context,
            "has_results": len(docs) > 0,
            "doc_count": len(docs),
        }


# Global instance
_kb_instance = None


def get_kb(use_json: bool = True) -> UnifiedKnowledgeBase:
    """Get or create the global KB instance."""
    global _kb_instance
    if _kb_instance is None:
        _kb_instance = UnifiedKnowledgeBase(use_json=use_json)
    return _kb_instance


if __name__ == "__main__":
    # Test the KB
    kb = get_kb()
    query = "conditions de service"
    result = kb.search_and_answer(query, k=3)
    
    print(f"Query: {query}")
    print(f"Documents found: {result['doc_count']}")
    print(f"\nContext:\n{result['context']}")
