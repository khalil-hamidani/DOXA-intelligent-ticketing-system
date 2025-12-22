# PIPELINE_IMPLEMENTATION_GUIDE.md

## RAG Pipeline Implementation Complete

This document describes the newly implemented RAG pipeline components that complement your existing agent-based system.

---

## Overview

**New Pipeline Structure**:
```
ai/
├── pipeline/                 # NEW: RAG pipeline stages
│   ├── __init__.py
│   ├── query_intelligence.py # Query validation, augmentation, multi-class classification
│   ├── retrieval.py          # Embedding-based vector search
│   ├── ranking.py            # Pluggable document ranking
│   ├── context.py            # Context augmentation & optimization
│   ├── answer.py             # LLM-based answer generation
│   └── orchestrator.py       # Complete pipeline orchestration
├── rag/                      # NEW: Embedding & vector store
│   ├── __init__.py
│   ├── embeddings.py         # Sentence-Transformers & Haystack integration
│   └── vector_store.py       # In-memory & Chroma vector stores
├── config/
│   ├── settings.py           # (existing)
│   └── pipeline_config.py    # NEW: Centralized configuration
└── agents/                   # (existing - unchanged)
```

---

## Key Components

### 1. Query Intelligence (`pipeline/query_intelligence.py`)

**Purpose**: Validate, augment, and classify queries with multi-class support.

**Classes**:
- `QueryValidator`: Sanity checks, low-signal detection
- `QueryAugmenter`: Query rephrasing, expansion, synonyms (using Agno + Mistral)
- `MulticlassClassifier`: Multi-class semantic classification (fixes double classification)
- `QueryPlanner`: Route queries and generate search strategy

**Usage**:
```python
from pipeline.query_intelligence import process_query_intelligence

result = process_query_intelligence(ticket, augment=True)
# Returns: validation, augmentation, summary, keywords, classification, plan
```

**Key Features**:
- ✅ Semantic class scoring (not hard categories)
- ✅ Multi-class support (e.g., ticket can be both "technique" and "facturation")
- ✅ Routing strategy based on relevance
- ✅ Fallback heuristic classification

---

### 2. Embeddings (`rag/embeddings.py`)

**Purpose**: Generate embeddings using sentence-transformers or Haystack.

**Classes**:
- `EmbeddingModel` (abstract): Base interface
- `SentenceTransformersEmbedder`: Local, offline embeddings
- `HaystackEmbedder`: Haystack AI integration (optional)
- `EmbeddingFactory`: Factory pattern

**Usage**:
```python
from rag.embeddings import EmbeddingFactory, embed_query

embedder = EmbeddingFactory.create(embedder_type="sentence_transformers")
query_embedding = embed_query("What is the issue?", embedder=embedder)
```

**Supported Models**:
- `all-MiniLM-L6-v2` (default, 384 dims, fast, offline)
- `all-mpnet-base-v2` (768 dims, better quality)
- Haystack quadrant embeddings (if installed)

---

### 3. Vector Store (`rag/vector_store.py`)

**Purpose**: Store and retrieve embeddings with similarity search.

**Classes**:
- `VectorStore` (abstract): Base interface
- `InMemoryVectorStore`: Fast, for testing/small datasets
- `ChromaVectorStore`: Persistent, production-ready
- `VectorStoreFactory`: Factory pattern

**Usage**:
```python
from rag.vector_store import VectorStoreFactory

store = VectorStoreFactory.create(store_type="in_memory")
store.add_documents(documents, embeddings)
results = store.search(query_embedding, top_k=5, threshold=0.4)
```

**Features**:
- ✅ Cosine similarity
- ✅ Configurable thresholds
- ✅ Metadata filtering
- ✅ Persistence (Chroma)

---

### 4. Retrieval (`pipeline/retrieval.py`)

**Purpose**: Semantic vector search with context awareness.

**Classes**:
- `VectorRetriever`: Core retrieval with embedder integration
- `SimilarityFilter`: Configurable filtering
- `ContextualRetriever`: Multi-step retrieval with fallback

**Usage**:
```python
from pipeline.retrieval import ContextualRetriever
from pipeline.query_intelligence import QueryPlanner

planner = QueryPlanner()
plan = planner.plan(ticket, classification_result)

retriever = ContextualRetriever(base_retriever)
retrieval_result = retriever.multi_step_retrieve(ticket, plan, fallback_enabled=True)
```

**Features**:
- ✅ Category-aware filtering
- ✅ Similarity threshold & relaxation
- ✅ Fallback strategy if no results
- ✅ Similarity statistics

---

### 5. Ranking (`pipeline/ranking.py`)

**Purpose**: Pluggable, configurable document ranking.

**Classes**:
- `Ranker` (abstract): Base interface
- `SemanticRanker`: Embedding similarity (default)
- `KeywordRanker`: BM25-like keyword matching
- `HybridRanker`: Semantic + keyword + metadata (recommended)
- `MetadataRanker`: Metadata-based boosting
- `RankingPipeline`: Orchestrator

**Usage**:
```python
from pipeline.ranking import RankingPipeline

ranker_pipeline = RankingPipeline(ranker_type="hybrid")
ranking_result = ranker_pipeline.rank(documents, query, max_results=10)

# Reconfigure at runtime
ranker_pipeline.reconfigure_ranker("keyword", query_weight=0.8)
```

**Features**:
- ✅ Pluggable ranker selection
- ✅ Configurable weights (hybrid)
- ✅ Ranking statistics
- ✅ Runtime reconfiguration

---

### 6. Context Augmentation (`pipeline/context.py`)

**Purpose**: Merge, chunk, and optimize context for LLM.

**Classes**:
- `DocumentMerger`: Concatenate, summary, or structured merging
- `ContextChunker`: Split content by token windows
- `ContextOptimizer`: Select documents to fit context window
- `ContextBuilder`: Format context for LLM prompts

**Usage**:
```python
from pipeline.context import ContextOptimizer, ContextBuilder

optimizer = ContextOptimizer(target_tokens=2000)
opt_result = optimizer.optimize(documents, query)

prompt = ContextBuilder.build_prompt_context(ticket, opt_result)
```

**Features**:
- ✅ Token-aware optimization
- ✅ Document selection prioritizing similarity
- ✅ Structured merging with metadata
- ✅ Fallback truncation

---

### 7. Answer Generation (`pipeline/answer.py`)

**Purpose**: LLM-based response generation with context.

**Classes**:
- `AnswerGenerator`: Core answer generation (Agno + Mistral)
- `ContextAwareAnswerGenerator`: Integration with context pipeline
- `ResponseValidator`: Confidence and validation checks

**Usage**:
```python
from pipeline.answer import ContextAwareAnswerGenerator

generator = ContextAwareAnswerGenerator()
answer_result = generator.generate_with_context(ticket, context_result)
```

**Features**:
- ✅ LLM-based generation (Mistral)
- ✅ Confidence scoring
- ✅ Escalation recommendations
- ✅ Fallback template responses

---

### 8. Pipeline Orchestrator (`pipeline/orchestrator.py`)

**Purpose**: Complete RAG pipeline orchestration.

**Classes**:
- `RAGPipeline`: Full orchestration with all stages
- `SimplifiedRAGPipeline`: Simplified API for common use cases

**Usage - Full Pipeline**:
```python
from pipeline.orchestrator import RAGPipeline
from config.pipeline_config import PipelineConfig

config = PipelineConfig.from_env()
rag = RAGPipeline(config)

# Add KB documents
rag.add_documents([
    {"id": "doc_1", "content": "...", "metadata": {"category": "technique"}}
])

# Process ticket
result = rag.process_ticket(ticket)
final_response = result["final_response"]
```

**Usage - Simplified**:
```python
from pipeline.orchestrator import SimplifiedRAGPipeline

rag = SimplifiedRAGPipeline()
rag.add_kb_documents(kb_entries)
answer = rag.answer_ticket(ticket)
```

**Pipeline Stages**:
1. Query Intelligence (validation, augmentation, classification)
2. Query Planning (routing, search strategy)
3. Retrieval (vector search with fallback)
4. Ranking (pluggable ranker)
5. Context Optimization (token-aware selection)
6. Answer Generation (LLM-based)
7. Validation (confidence & issue checks)

---

## Configuration (`config/pipeline_config.py`)

**Configuration Classes**:
- `EmbeddingConfig`: Embedder type, model name
- `VectorStoreConfig`: Store type, persistence
- `RetrieverConfig`: Top-k, threshold, filters
- `RankerConfig`: Ranker type, weights
- `ContextConfig`: Token limits, merging strategy
- `AnswerConfig`: Confidence, model, temperature
- `PipelineConfig`: Complete configuration

**Usage**:
```python
from config.pipeline_config import PipelineConfig, get_pipeline_config, set_pipeline_config

# Load from environment
config = get_pipeline_config()

# Create custom config
custom_config = PipelineConfig.default()
custom_config.ranker.ranker_type = "semantic"
set_pipeline_config(custom_config)
```

**Environment Variables**:
```bash
# Embeddings
EMBEDDING_TYPE=sentence_transformers
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Vector Store
VECTOR_STORE_TYPE=in_memory  # or "chroma"
VECTOR_STORE_PERSIST_DIR=/path/to/persist

# Retriever
RETRIEVER_TOP_K=5
RETRIEVER_THRESHOLD=0.4

# Ranker
RANKER_TYPE=hybrid

# Context
CONTEXT_MAX_TOKENS=4000
CONTEXT_TARGET_TOKENS=2000

# Answer
ANSWER_MIN_CONFIDENCE=0.5
MISTRAL_MODEL_ID=mistral-small-latest
```

---

## Integration with Existing Code

### Non-Breaking Integration

Your existing `agents/` system remains **unchanged**. The new pipeline components are **additive**:

```python
from agents.orchestrator import process_ticket as agent_process_ticket
from pipeline.orchestrator import RAGPipeline

# Option 1: Use existing agent-based pipeline
result_agent = agent_process_ticket(ticket)

# Option 2: Use new RAG pipeline
rag = RAGPipeline()
result_rag = rag.process_ticket(ticket)

# Option 3: Hybrid - Agent validation + RAG retrieval
result_agent_validation = validate_ticket(ticket)
if result_agent_validation.get("valid"):
    result_rag = rag.process_ticket(ticket)
```

### Reuse of Existing Components

- **Validation**: Your `validator.py` can still run first
- **Scoring**: Your `scorer.py` still computes priority
- **Classification**: New `MulticlassClassifier` enhances existing classification
- **Response Composition**: Both pipelines can use `response_composer.py`

---

## Missing Components Addressed

| **Component** | **Status** | **Location** | **Notes** |
|---------------|-----------|------------|----------|
| Query validation | ✅ Enhanced | `query_intelligence.py` | Low-signal detection added |
| Query augmentation | ✅ NEW | `query_intelligence.py` | Rephrasing, expansion, synonyms |
| Keyword extraction | ✅ Existing | Used by query_intelligence | From `query_analyzer.py` |
| Multi-class classification | ✅ NEW | `MulticlassClassifier` | Fixes double classification |
| Embedding generation | ✅ NEW | `embeddings.py` | Sentence-Transformers + Haystack |
| Vector retrieval | ✅ NEW | `retrieval.py` | Cosine similarity, thresholds |
| Ranking | ✅ NEW | `ranking.py` | Pluggable rankers (semantic, hybrid, etc.) |
| Context augmentation | ✅ NEW | `context.py` | Merging, chunking, optimization |
| Answer generation | ✅ Existing | Enhanced in `answer.py` | With context awareness |

---

## Example: Full Workflow

```python
from models import Ticket
from pipeline.orchestrator import RAGPipeline
from config.pipeline_config import PipelineConfig

# 1. Create and configure pipeline
config = PipelineConfig.default()
rag = RAGPipeline(config)

# 2. Add KB documents
kb_docs = [
    {
        "id": "tech_restart",
        "content": "To fix crashes, try restarting the application...",
        "metadata": {"category": "technique"}
    },
    {
        "id": "billing_invoice",
        "content": "View your invoices in the Account > Billing section...",
        "metadata": {"category": "facturation"}
    }
]
rag.add_documents(kb_docs)

# 3. Create ticket
ticket = Ticket(
    id="ticket_001",
    client_name="Alice",
    email="alice@example.com",
    subject="Application keeps crashing",
    description="The app crashes every time I try to export data..."
)

# 4. Process through full pipeline
result = rag.process_ticket(ticket)

# 5. Access results
print("Query Intelligence:", result["stages"]["query_intelligence"]["classification"])
print("Retrieved Docs:", result["stages"]["retrieval"]["retrieved_count"])
print("Final Response:", result["final_response"])
```

---

## Performance Considerations

**Embeddings** (First run: 30-60s, cached after):
- `all-MiniLM-L6-v2`: Fast, suitable for real-time
- `all-mpnet-base-v2`: Better quality, slower

**Vector Store**:
- `in_memory`: Suitable for <10k documents
- `chroma`: Production-ready, persistent

**Ranking**:
- `semantic`: Fastest, uses pre-computed scores
- `hybrid`: Balanced quality/speed (recommended)
- `keyword`: Good for keyword-heavy queries

**Context**:
- Target 2000 tokens (≈ 8000 chars) for optimal LLM performance
- Adjust `CONTEXT_TARGET_TOKENS` based on your LLM's context window

---

## Testing & Validation

```python
from pipeline.answer import ResponseValidator

validator = ResponseValidator(min_confidence=0.5)
validation = validator.validate(answer_result)

if not validation["valid"]:
    print("Issues:", validation["issues"])
    print("Recommendations:", validation["recommendations"])
```

---

## Future Extensions

1. **Feedback Loop**: Track user feedback to improve ranking
2. **Fine-tuning**: Fine-tune embedder on domain-specific data
3. **Caching**: Cache embeddings for repeated queries
4. **A/B Testing**: Compare rankers or configurations
5. **Analytics**: Track retrieval accuracy, answer quality
6. **Multi-language**: Extend to support multiple languages

---

## Summary

✅ **Complete RAG pipeline implemented**
✅ **Non-breaking integration with existing agents**
✅ **Pluggable, configurable components**
✅ **Production-ready code patterns**
✅ **Comprehensive error handling & fallbacks**
✅ **Clear separation of concerns**
✅ **Ready for agent orchestrator integration**

The pipeline is modular and designed for integration into your agent system. Each stage can be independently configured, replaced, or extended.
