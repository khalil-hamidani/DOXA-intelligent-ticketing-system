# config/pipeline_config.py
"""Pipeline configuration for RAG stages.

Centralizes all configuration for embeddings, vector store, rankers, etc.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class EmbeddingConfig:
    """Embedding model configuration."""
    embedder_type: str = "sentence_transformers"  # "sentence_transformers" | "haystack"
    model_name: str = "all-MiniLM-L6-v2"  # Fast 384-dim model
    # Alternative: "all-mpnet-base-v2" (768-dim, better quality)
    
    @classmethod
    def from_env(cls) -> "EmbeddingConfig":
        """Load from environment variables."""
        return cls(
            embedder_type=os.environ.get("EMBEDDING_TYPE", "sentence_transformers"),
            model_name=os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        )


@dataclass
class VectorStoreConfig:
    """Vector store configuration."""
    store_type: str = "in_memory"  # "in_memory" | "chroma"
    collection_name: str = "documents"
    persist_dir: Optional[str] = None  # For Chroma persistence
    
    @classmethod
    def from_env(cls) -> "VectorStoreConfig":
        """Load from environment variables."""
        return cls(
            store_type=os.environ.get("VECTOR_STORE_TYPE", "in_memory"),
            persist_dir=os.environ.get("VECTOR_STORE_PERSIST_DIR")
        )


@dataclass
class RankerConfig:
    """Ranker configuration."""
    ranker_type: str = "hybrid"  # "semantic" | "keyword" | "hybrid" | "metadata"
    semantic_weight: float = 0.6
    keyword_weight: float = 0.2
    metadata_weight: float = 0.2
    
    @classmethod
    def from_env(cls) -> "RankerConfig":
        """Load from environment variables."""
        return cls(
            ranker_type=os.environ.get("RANKER_TYPE", "hybrid")
        )


@dataclass
class RetrieverConfig:
    """Retriever configuration."""
    top_k: int = 5
    similarity_threshold: float = 0.4
    similarity_threshold_relaxed: float = 0.2  # For fallback
    max_results: int = 10
    filters: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_env(cls) -> "RetrieverConfig":
        """Load from environment variables."""
        return cls(
            top_k=int(os.environ.get("RETRIEVER_TOP_K", "5")),
            similarity_threshold=float(os.environ.get("RETRIEVER_THRESHOLD", "0.4"))
        )


@dataclass
class ContextConfig:
    """Context augmentation configuration."""
    max_tokens: int = 4000  # Total context window size
    chunk_overlap: int = 100
    merging_strategy: str = "structured"  # "concatenate" | "summary" | "structured"
    target_tokens: int = 2000  # Ideal context size for answer generation
    prioritize_similarity: bool = True
    
    @classmethod
    def from_env(cls) -> "ContextConfig":
        """Load from environment variables."""
        return cls(
            max_tokens=int(os.environ.get("CONTEXT_MAX_TOKENS", "4000")),
            target_tokens=int(os.environ.get("CONTEXT_TARGET_TOKENS", "2000"))
        )


@dataclass
class AnswerConfig:
    """Answer generation configuration."""
    use_context: bool = True
    min_confidence: float = 0.5
    model_id: str = "mistral-small-latest"  # Mistral model
    temperature: float = 0.3
    
    @classmethod
    def from_env(cls) -> "AnswerConfig":
        """Load from environment variables."""
        return cls(
            use_context=os.environ.get("ANSWER_USE_CONTEXT", "true").lower() == "true",
            min_confidence=float(os.environ.get("ANSWER_MIN_CONFIDENCE", "0.5")),
            model_id=os.environ.get("MISTRAL_MODEL_ID", "mistral-small-latest")
        )


@dataclass
class PipelineConfig:
    """Complete pipeline configuration."""
    embedding: EmbeddingConfig
    vector_store: VectorStoreConfig
    retriever: RetrieverConfig
    ranker: RankerConfig
    context: ContextConfig
    answer: AnswerConfig
    
    @classmethod
    def from_env(cls) -> "PipelineConfig":
        """Load all configuration from environment."""
        return cls(
            embedding=EmbeddingConfig.from_env(),
            vector_store=VectorStoreConfig.from_env(),
            retriever=RetrieverConfig.from_env(),
            ranker=RankerConfig.from_env(),
            context=ContextConfig.from_env(),
            answer=AnswerConfig.from_env()
        )
    
    @classmethod
    def default(cls) -> "PipelineConfig":
        """Create default configuration."""
        return cls(
            embedding=EmbeddingConfig(),
            vector_store=VectorStoreConfig(),
            retriever=RetrieverConfig(),
            ranker=RankerConfig(),
            context=ContextConfig(),
            answer=AnswerConfig()
        )


# Global pipeline config instance
_pipeline_config: Optional[PipelineConfig] = None


def get_pipeline_config() -> PipelineConfig:
    """Get global pipeline configuration."""
    global _pipeline_config
    if _pipeline_config is None:
        _pipeline_config = PipelineConfig.from_env()
    return _pipeline_config


def set_pipeline_config(config: PipelineConfig):
    """Set global pipeline configuration."""
    global _pipeline_config
    _pipeline_config = config
