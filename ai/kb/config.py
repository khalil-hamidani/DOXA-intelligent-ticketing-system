"""
KB Configuration Module

Manages all configuration settings for PDF ingestion with Mistral OCR,
embedding generation with Haystack AI, and Qdrant vector database storage.
"""

from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class EmbeddingModel(str, Enum):
    """Supported embedding models for Haystack AI."""
    SENTENCE_TRANSFORMERS = "sentence-transformers/all-MiniLM-L6-v2"
    MISTRAL_EMBED = "mistral/Mistral-7B-Instruct-v0.1"
    MULTILINGUAL = "sentence-transformers/multilingual-e5-base"


class KBConfig(BaseModel):
    """Configuration for the Knowledge Base pipeline with Mistral OCR + Haystack + Qdrant."""
    
    # PDF Processing Settings
    pdf_input_path: Path = Field(
        default=Path("ai/kb/documents"),
        description="Path to PDF documents"
    )
    enable_mistral_ocr: bool = Field(
        default=True,
        description="Enable Mistral OCR for scanned PDFs"
    )
    mistral_api_key: Optional[str] = Field(
        default=None,
        description="Mistral API key for OCR"
    )
    
    # Chunking Settings
    chunk_size: int = Field(
        default=512,
        description="Size of text chunks in characters"
    )
    chunk_overlap: int = Field(
        default=102,
        description="Overlap between chunks in characters"
    )
    use_title_splits: bool = Field(
        default=True,
        description="Use title-based semantic splits (## headers)"
    )
    
    # Embedding Settings
    embedding_model: EmbeddingModel = Field(
        default=EmbeddingModel.SENTENCE_TRANSFORMERS,
        description="Embedding model to use with Haystack"
    )
    embedding_dim: int = Field(
        default=384,
        description="Dimension of embeddings"
    )
    batch_embedding_size: int = Field(
        default=32,
        description="Batch size for embedding generation"
    )
    
    # Qdrant Vector Database Settings
    qdrant_host: str = Field(
        default="localhost",
        description="Qdrant server host"
    )
    qdrant_port: int = Field(
        default=6333,
        description="Qdrant server port"
    )
    qdrant_collection_name: str = Field(
        default="doxa_kb",
        description="Qdrant collection name"
    )
    
    # Retrieval Settings
    top_k: int = Field(
        default=5,
        description="Number of top results to retrieve"
    )
    similarity_threshold: float = Field(
        default=0.5,
        description="Minimum cosine similarity score"
    )
    
    # Storage Settings
    document_store_path: Path = Field(
        default=Path("ai/kb/document_store"),
        description="Path to store documents metadata"
    )

    class Config:
        """Pydantic config."""
        use_enum_values = False


def get_default_config() -> KBConfig:
    """Get default KB configuration."""
    return KBConfig()


def load_config_from_env() -> KBConfig:
    """Load configuration from environment variables."""
    import os
    
    config_dict = {}
    
    # PDF settings
    if os.getenv("KB_PDF_PATH"):
        config_dict["pdf_input_path"] = Path(os.getenv("KB_PDF_PATH"))
    if os.getenv("KB_MISTRAL_API_KEY"):
        config_dict["mistral_api_key"] = os.getenv("KB_MISTRAL_API_KEY")
    
    # Chunking settings
    if os.getenv("KB_CHUNK_SIZE"):
        config_dict["chunk_size"] = int(os.getenv("KB_CHUNK_SIZE"))
    if os.getenv("KB_CHUNK_OVERLAP"):
        config_dict["chunk_overlap"] = int(os.getenv("KB_CHUNK_OVERLAP"))
    
    # Qdrant settings
    if os.getenv("KB_QDRANT_HOST"):
        config_dict["qdrant_host"] = os.getenv("KB_QDRANT_HOST")
    if os.getenv("KB_QDRANT_PORT"):
        config_dict["qdrant_port"] = int(os.getenv("KB_QDRANT_PORT"))
    
    # Retrieval settings
    if os.getenv("KB_TOP_K"):
        config_dict["top_k"] = int(os.getenv("KB_TOP_K"))
    if os.getenv("KB_SIMILARITY_THRESHOLD"):
        config_dict["similarity_threshold"] = float(os.getenv("KB_SIMILARITY_THRESHOLD"))
    
    return KBConfig(**config_dict) if config_dict else get_default_config()
