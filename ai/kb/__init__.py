"""
Knowledge Base Package

Production-grade KB ingestion and retrieval pipeline for DOXA ticket system.

Focused implementation using:
- PDF-only document ingestion
- Mistral OCR for scanned PDF processing
- Semantic chunking with hierarchical ## title organization
- Haystack AI embeddings with Sentence Transformers
- Qdrant vector database with cosine similarity
- Direct integration with ticket processing agents
"""

from kb.config import (
    KBConfig,
    EmbeddingModel,
    get_default_config,
    load_config_from_env,
)

from kb.ingest import (
    MistralOCRProcessor,
    PDFIngestor,
    DocumentChunk,
)

from kb.embeddings import (
    HaystackEmbeddingStore,
)

from kb.retriever import (
    HaystackRetriever,
    SearchResult,
    TicketKBInterface,
)

__all__ = [
    # Config
    "KBConfig",
    "EmbeddingModel",
    "get_default_config",
    "load_config_from_env",
    # Ingestion (PDF + Mistral OCR)
    "MistralOCRProcessor",
    "PDFIngestor",
    "DocumentChunk",
    # Embeddings (Haystack + Qdrant)
    "HaystackEmbeddingStore",
    # Retrieval (Haystack Retriever)
    "HaystackRetriever",
    "SearchResult",
    "TicketKBInterface",
]

__version__ = "2.0.0"
