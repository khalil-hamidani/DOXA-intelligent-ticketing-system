# pipeline/__init__.py
"""RAG Pipeline: Query Intelligence -> Retrieval -> Ranking -> Context -> Answer.

This package provides modular, configurable pipeline stages for ticket resolution:
1. Query Intelligence: Validation, augmentation, multi-class classification
2. Retrieval: Embedding-based vector search with similarity filtering
3. Ranking: Pluggable rankers (semantic, keyword, hybrid, metadata)
4. Context Augmentation: Document merging, chunking, and optimization
5. Answer Generation: LLM-based response with augmented context
"""

from pipeline.query_intelligence import (
    QueryValidator,
    QueryAugmenter,
    MulticlassClassifier,
    QueryPlanner,
    process_query_intelligence
)

from pipeline.retrieval import (
    VectorRetriever,
    SimilarityFilter,
    ContextualRetriever
)

from pipeline.ranking import (
    Ranker,
    SemanticRanker,
    KeywordRanker,
    HybridRanker,
    RankingPipeline
)

from pipeline.context import (
    DocumentMerger,
    ContextChunker,
    ContextOptimizer,
    ContextBuilder
)

from pipeline.answer import (
    AnswerGenerator,
    ContextAwareAnswerGenerator,
    ResponseValidator
)

from pipeline.orchestrator import (
    RAGPipeline,
    SimplifiedRAGPipeline
)

__all__ = [
    # Query Intelligence
    "QueryValidator",
    "QueryAugmenter",
    "MulticlassClassifier",
    "QueryPlanner",
    "process_query_intelligence",
    # Retrieval
    "VectorRetriever",
    "SimilarityFilter",
    "ContextualRetriever",
    # Ranking
    "Ranker",
    "SemanticRanker",
    "KeywordRanker",
    "HybridRanker",
    "RankingPipeline",
    # Context
    "DocumentMerger",
    "ContextChunker",
    "ContextOptimizer",
    "ContextBuilder",
    # Answer
    "AnswerGenerator",
    "ContextAwareAnswerGenerator",
    "ResponseValidator",
    # Orchestrator
    "RAGPipeline",
    "SimplifiedRAGPipeline"
]
