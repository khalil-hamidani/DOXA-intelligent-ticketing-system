# rag/__init__.py
"""RAG (Retrieval-Augmented Generation) Module.

Provides embeddings, vector storage, and retrieval components.
"""

from rag.embeddings import (
    EmbeddingModel,
    SentenceTransformersEmbedder,
    HaystackEmbedder,
    EmbeddingFactory,
    embed_texts,
    embed_query
)

from rag.vector_store import (
    VectorStore,
    InMemoryVectorStore,
    ChromaVectorStore,
    VectorStoreFactory
)

__all__ = [
    # Embeddings
    "EmbeddingModel",
    "SentenceTransformersEmbedder",
    "HaystackEmbedder",
    "EmbeddingFactory",
    "embed_texts",
    "embed_query",
    # Vector Store
    "VectorStore",
    "InMemoryVectorStore",
    "ChromaVectorStore",
    "VectorStoreFactory"
]
