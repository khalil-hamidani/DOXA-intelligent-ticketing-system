# rag/embeddings.py
"""Embedding models and generation.

Supports:
- Sentence-Transformers embeddings (local, offline)
- Haystack AI integration
- Pluggable embedding models
"""

from typing import List, Optional, Dict
import numpy as np
from abc import ABC, abstractmethod
import os

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    from haystack.components.embedders import SentenceTransformersDocumentEmbedder, SentenceTransformersQueryEmbedder
    HAYSTACK_AVAILABLE = True
except ImportError:
    HAYSTACK_AVAILABLE = False


class EmbeddingModel(ABC):
    """Abstract embedding model interface."""
    
    @abstractmethod
    def embed_documents(self, texts: List[str]) -> np.ndarray:
        """Embed multiple documents.
        
        Args:
            texts: List of text strings
            
        Returns:
            numpy array of shape (len(texts), embedding_dim)
        """
        pass
    
    @abstractmethod
    def embed_query(self, text: str) -> np.ndarray:
        """Embed a single query.
        
        Args:
            text: Query text
            
        Returns:
            numpy array of shape (embedding_dim,)
        """
        pass
    
    @abstractmethod
    def get_embedding_dim(self) -> int:
        """Get embedding dimension."""
        pass


class SentenceTransformersEmbedder(EmbeddingModel):
    """Sentence-Transformers based embedder (local, offline)."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize embedder.
        
        Args:
            model_name: HuggingFace model name
                - "all-MiniLM-L6-v2": Fast, 384 dims
                - "all-mpnet-base-v2": Better quality, 768 dims
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError("sentence-transformers not installed. pip install sentence-transformers")
        
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self._embedding_dim = self.model.get_sentence_embedding_dimension()
    
    def embed_documents(self, texts: List[str]) -> np.ndarray:
        """Embed documents using sentence-transformers."""
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return embeddings
    
    def embed_query(self, text: str) -> np.ndarray:
        """Embed query using sentence-transformers."""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding
    
    def get_embedding_dim(self) -> int:
        """Get embedding dimension."""
        return self._embedding_dim


class HaystackEmbedder(EmbeddingModel):
    """Haystack AI embedder wrapper."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize Haystack embedder.
        
        Args:
            model_name: HuggingFace model name
        """
        if not HAYSTACK_AVAILABLE:
            raise ImportError("haystack-ai not installed. pip install haystack-ai")
        
        self.model_name = model_name
        self._doc_embedder = SentenceTransformersDocumentEmbedder(model=model_name)
        self._query_embedder = SentenceTransformersQueryEmbedder(model=model_name)
        
        # Initialize embedders (run method to set up)
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".txt") as f:
            f.write(b"test")
            f.flush()
            self._embedding_dim = len(self._query_embedder.run(text="test")["embedding"])
    
    def embed_documents(self, texts: List[str]) -> np.ndarray:
        """Embed documents using Haystack."""
        from haystack import Document
        docs = [Document(content=text) for text in texts]
        result = self._doc_embedder.run(documents=docs)
        embeddings = np.array([doc.embedding for doc in result["documents"]])
        return embeddings
    
    def embed_query(self, text: str) -> np.ndarray:
        """Embed query using Haystack."""
        result = self._query_embedder.run(text=text)
        return np.array(result["embedding"])
    
    def get_embedding_dim(self) -> int:
        """Get embedding dimension."""
        return self._embedding_dim


class EmbeddingFactory:
    """Factory for creating embedders."""
    
    @staticmethod
    def create(
        embedder_type: str = "sentence_transformers",
        model_name: Optional[str] = None,
        **kwargs
    ) -> EmbeddingModel:
        """Create an embedder.
        
        Args:
            embedder_type: "sentence_transformers" | "haystack"
            model_name: HuggingFace model name (default: all-MiniLM-L6-v2)
            **kwargs: Additional arguments passed to embedder
            
        Returns:
            EmbeddingModel instance
        """
        if model_name is None:
            model_name = os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        
        if embedder_type == "sentence_transformers":
            return SentenceTransformersEmbedder(model_name=model_name)
        elif embedder_type == "haystack":
            return HaystackEmbedder(model_name=model_name)
        else:
            raise ValueError(f"Unknown embedder type: {embedder_type}")


def embed_texts(texts: List[str], embedder: Optional[EmbeddingModel] = None) -> np.ndarray:
    """Utility function to embed texts.
    
    Args:
        texts: List of texts to embed
        embedder: EmbeddingModel instance (default: SentenceTransformersEmbedder)
        
    Returns:
        numpy array of embeddings
    """
    if embedder is None:
        embedder = EmbeddingFactory.create()
    
    return embedder.embed_documents(texts)


def embed_query(text: str, embedder: Optional[EmbeddingModel] = None) -> np.ndarray:
    """Utility function to embed a query.
    
    Args:
        text: Query text
        embedder: EmbeddingModel instance (default: SentenceTransformersEmbedder)
        
    Returns:
        numpy array of query embedding
    """
    if embedder is None:
        embedder = EmbeddingFactory.create()
    
    return embedder.embed_query(text)
