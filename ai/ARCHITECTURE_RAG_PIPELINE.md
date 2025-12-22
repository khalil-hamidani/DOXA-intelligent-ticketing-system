# ARCHITECTURE_RAG_PIPELINE.md

## RAG Pipeline Architecture - Updated Analysis

**Last Updated**: December 22, 2025  
**Status**: Production Ready  
**Integration**: Full integration with Agent-based ticket processing system

### System Overview

The RAG (Retrieval-Augmented Generation) pipeline is a multi-stage system that:
1. Processes tickets through intelligent query understanding
2. Retrieves relevant knowledge base documents via vector similarity
3. Ranks and optimizes context for LLM consumption
4. Generates contextual responses with confidence scores
5. Validates and escalates as needed

---

### High-Level System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     TICKET INPUT                                │
│  (subject, description, client_name, email, etc.)               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              STAGE 1: QUERY INTELLIGENCE                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ QueryValidator: Sanity checks, low-signal detection      │   │
│  │ → Output: {valid, reasons, signals}                      │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ QueryAugmenter: Rephrasing, expansion, synonyms (LLM)    │   │
│  │ → Output: {rephrased, expansion, synonyms, context}      │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ MulticlassClassifier: Per-class semantic scores (LLM)     │   │
│  │ → Output: {primary_class, scores, relevant_classes}      │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ QueryPlanner: Route, search params, strategy              │   │
│  │ → Output: {route, search_query, search_params}           │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    [Valid? → Continue]
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│           STAGE 2a: EMBEDDING GENERATION                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ EmbeddingFactory → EmbeddingModel                         │   │
│  │  - SentenceTransformersEmbedder (local, offline)          │   │
│  │  - HaystackEmbedder (optional)                            │   │
│  │ Query → embedding vector (384 or 768 dims)               │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│          STAGE 2b: VECTOR RETRIEVAL                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ VectorRetriever: Search vector store                      │   │
│  │  - Cosine similarity computation                          │   │
│  │  - Threshold filtering (default 0.4)                      │   │
│  │  - Top-k selection (default 5)                            │   │
│  │ → Output: {results, similarity_matrix, stats}            │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ ContextualRetriever: Category-aware search               │   │
│  │  - Primary retrieval (with threshold)                     │   │
│  │  - Fallback retrieval (relaxed threshold 0.2)            │   │
│  │ → Output: {results, augmentation, fallback_applied}      │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
          [No results? → Fallback retrieval with lower threshold]
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│               STAGE 3: DOCUMENT RANKING                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ RankingPipeline (pluggable)                              │   │
│  │  - SemanticRanker: Embedding similarity                   │   │
│  │  - KeywordRanker: BM25-like keyword matching              │   │
│  │  - HybridRanker: Semantic + keyword + metadata (default)  │   │
│  │  - MetadataRanker: Category/priority/recency              │   │
│  │ → Output: {ranked_documents, scores, top_result}         │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│          STAGE 4: CONTEXT AUGMENTATION                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ ContextOptimizer: Token-aware document selection          │   │
│  │  - Greedy selection to fit target_tokens (default 2000)   │   │
│  │  - Priority by similarity scores                          │   │
│  │  - Graceful truncation for last doc                       │   │
│  │ → Output: {selected_docs, optimization_info}             │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ DocumentMerger: Merge selected docs                       │   │
│  │  - concatenate: Simple join                               │   │
│  │  - summary: Keep top-3 full, summarize rest              │   │
│  │  - structured: Include metadata & relevance              │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ ContextBuilder: Format for LLM consumption                │   │
│  │  - build_prompt_context: Formatted prompt                 │   │
│  │  - build_structured_context: Dict format                  │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│            STAGE 5: ANSWER GENERATION                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ AnswerGenerator: LLM-based response (Agno + Mistral)      │   │
│  │  - Use augmented context + query                          │   │
│  │  - Generate answer, confidence, escalation flag           │   │
│  │ → Output: {answer, confidence, escalation, actions}      │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ ContextAwareAnswerGenerator: Integrate with context       │   │
│  │  - Format final response for client                       │   │
│  │ → Output: {final_response, escalation_recommended}        │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              STAGE 6: VALIDATION                                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ ResponseValidator: QA checks                              │   │
│  │  - Answer length (min 50 chars)                           │   │
│  │  - Confidence threshold (default 0.5)                     │   │
│  │  - Escalation detection                                   │   │
│  │ → Output: {valid, issues, recommendations}               │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │ FINAL RESPONSE │
                    │  (or escalate) │
                    └────────────────┘
```

---

### Actual Folder Structure & Component Mapping

```
ai/
├── agents/                          ← Agent implementations
│   ├── validator.py                 ← Ticket validation
│   ├── scorer.py                    ← Priority/severity scoring
│   ├── query_analyzer.py            ← Query analysis & reformulation
│   ├── unified_classifier.py        ← Category classification
│   ├── query_planner.py             ← Resolution path planning
│   ├── evaluator.py                 ← Ticket evaluation
│   ├── response_composer.py         ← Response generation
│   ├── feedback_handler.py          ← Feedback processing
│   ├── escalation_manager.py        ← Escalation handling
│   ├── orchestrator.py              ← Agent orchestration
│   └── __init__.py
│
├── pipeline/                        ← Processing pipelines
│   ├── __init__.py
│   ├── retrieval.py                 ← Vector retrieval pipeline
│   ├── ranking.py                   ← Document ranking
│   ├── context.py                   ← Context augmentation
│   ├── answer.py                    ← Answer generation
│   ├── query_intelligence.py        ← Query processing
│   └── orchestrator.py              ← Pipeline orchestration
│
├── rag/                             ← RAG system core
│   ├── __init__.py
│   ├── embeddings.py                ← Embedding models & factory
│   └── vector_store.py              ← Vector store implementations
│
├── kb/                              ← Knowledge base management
│   ├── __init__.py
│   ├── kb_manager.py                ← KB lifecycle management
│   ├── retriever.py                 ← KB retrieval interface
│   ├── vector_store.py              ← Vector storage for KB
│   ├── embeddings.py                ← Embedding utilities
│   ├── ingest.py                    ← Document ingestion
│   ├── chunking.py                  ← Document chunking
│   ├── config.py                    ← KB configuration
│   ├── test_integration.py          ← Integration tests
│   └── README.md
│
├── app/                             ← Application layer
│   ├── main.py                      ← FastAPI application
│   ├── clients/
│   │   └── backend_client.py        ← Backend API client
│   ├── pipeline/
│   │   ├── evaluator.py             ← Evaluation wrapper
│   │   ├── query_analyzer.py        ← Analysis wrapper
│   │   ├── response_composer.py     ← Composition wrapper
│   │   └── solution_finder.py       ← Solution finding
│   ├── rag/
│   │   ├── retriever.py             ← RAG retriever interface
│   │   └── vector_store.py          ← Vector store wrapper
│   └── schemas/
│       └── ai_contracts.py          ← API contracts
│
├── config/                          ← Configuration management
│   ├── settings.py                  ← Application settings
│   ├── pipeline_config.py           ← Pipeline configuration
│   └── __pycache__/
│
├── models/                          ← Data models
│   └── schemas.py                   ← Pydantic schemas
│
├── utils/                           ← Utilities
│   ├── llm_client.py                ← LLM client wrapper
│   └── metrics.py                   ← Metrics tracking
│
├── data/                            ← Data storage
│   ├── tickets.json                 ← Sample tickets
│   └── metrics.json                 ← Performance metrics
│
├── tests/                           ← Test suite
│   ├── test_agents.py
│   ├── test_comprehensive.py
│   ├── test_system.py
│   └── __init__.py
│
├── models.py                        ← Core Ticket model
├── main.py                          ← Entry point
└── requirements.txt                 ← Dependencies
```

---

### Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────┐
│              RAGPipeline (Orchestrator)                 │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │ QueryIntelligence Processor (pipeline/)          │   │
│  │  • query_intelligence.py                         │   │
│  │    - QueryValidator (agents/validator.py)        │   │
│  │    - QueryAnalyzer (agents/query_analyzer.py)    │   │
│  │    - UnifiedClassifier (agents/unified_...)      │   │
│  │    - QueryPlanner (agents/query_planner.py)      │   │
│  └──────────┬───────────────────────────────────────┘   │
│             │                                           │
│  ┌──────────▼───────────────────────────────────────┐   │
│  │ Retrieval Pipeline                              │   │
│  │                                                  │   │
│  │  ┌──────────────────────────────────────────┐   │   │
│  │  │ EmbeddingFactory                          │   │   │
│  │  │  → SentenceTransformersEmbedder          │   │   │
│  │  │  → HaystackEmbedder (optional)           │   │   │
│  │  └──────────────────────────────────────────┘   │   │
│  │                    │                             │   │
│  │  ┌──────────────────▼──────────────────────┐   │   │
│  │  │ VectorStoreFactory                       │   │   │
│  │  │  → InMemoryVectorStore                   │   │   │
│  │  │  → ChromaVectorStore                     │   │   │
│  │  └──────────────────────────────────────────┘   │   │
│  │                    │                             │   │
│  │  ┌──────────────────▼──────────────────────┐   │   │
│  │  │ VectorRetriever                          │   │   │
│  │  │  • Cosine similarity                     │   │   │
│  │  │  • Threshold filtering                   │   │   │
│  │  │  • Similarity matrix                     │   │   │
│  │  └──────────────────────────────────────────┘   │   │
│  │                    │                             │   │
│  │  ┌──────────────────▼──────────────────────┐   │   │
│  │  │ ContextualRetriever                      │   │   │
│  │  │  • Category-aware filtering              │   │   │
│  │  │  • Multi-step with fallback              │   │   │
│  │  │  • Similarity statistics                 │   │   │
│  │  └──────────────────────────────────────────┘   │   │
│  └──────────┬───────────────────────────────────────┘   │
│             │                                           │
│  ┌──────────▼───────────────────────────────────────┐   │
│  │ Ranking Pipeline                                │   │
│  │  • RankerFactory                                │   │
│  │    → SemanticRanker                             │   │
│  │    → KeywordRanker                              │   │
│  │    → HybridRanker                               │   │
│  │    → MetadataRanker                             │   │
│  │  • Runtime reconfiguration                      │   │
│  └──────────┬───────────────────────────────────────┘   │
│             │                                           │
│  ┌──────────▼───────────────────────────────────────┐   │
│  │ Context Augmentation Pipeline                   │   │
│  │  • DocumentMerger                               │   │
│  │  • ContextOptimizer                             │   │
│  │  • ContextBuilder                               │   │
│  └──────────┬───────────────────────────────────────┘   │
│             │                                           │
│  ┌──────────▼───────────────────────────────────────┐   │
│  │ Answer Generation Pipeline                      │   │
│  │  • AnswerGenerator (Agent: Agno+Mistral)       │   │
│  │  • ContextAwareAnswerGenerator                  │   │
│  │  • ResponseValidator                            │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

### Data Flow: Object Model

```
INPUT (models.py - Ticket):
  {
    id: str,
    subject: str,
    description: str,
    client_name: str,
    email: str,
    category: str (optional),
    priority: int (optional)
  }
  
        ↓
  
STAGE 1 - Query Validation & Analysis (agents/):
  {
    is_valid: bool,
    keywords: [str],
    reformulation: str,
    category: str,
    priority_score: int,
    confidence: float
  }
  
        ↓
  
STAGE 2 - Embedding & Retrieval (pipeline/retrieval.py):
  {
    query_embedding: [float] (384 dims),
    retrieved_documents: [
      {
        id: str,
        content: str,
        similarity: float (0.0-1.0),
        metadata: {category, source, ...}
      }
    ],
    total_similar_docs: int,
    avg_similarity: float
  }
  
        ↓
  
STAGE 3 - Ranking (pipeline/ranking.py):
  {
    ranked_documents: [
      {
        ...doc,
        rank_score: float,
        rank: int,
        ranker_type: str
      }
    ],
    top_result: {...},
    ranking_strategy: str
  }
  
        ↓
  
STAGE 4 - Context Building (pipeline/context.py):
  {
    selected_documents: [...],
    context_string: str,
    token_count: int,
    token_budget: int,
    truncation_applied: bool,
    optimization_ratio: float
  }
  
        ↓
  
STAGE 5 - Answer Generation (agents/response_composer.py):
  {
    answer: str,
    confidence: float (0.0-1.0),
    sources_used: [str],
    suggested_actions: [str],
    escalation_recommended: bool,
    escalation_reason: str (optional)
  }
  
        ↓
  
STAGE 6 - Evaluation & Escalation (agents/evaluator.py):
  {
    final_response: str (formatted),
    priority_score: int,
    escalation_flag: bool,
    handler_assigned: str (optional),
    confidence_final: float
  }
  
        ↓
  
OUTPUT:
  Response sent to client / escalated to human agent
```

---

## 4. Agent Integration Points

The RAG pipeline is orchestrated through a set of specialized agents, each handling distinct ticket processing stages:

| Agent | Module | Role | Input | Output | RAG Integration |
|-------|--------|------|-------|--------|-----------------|
| **Ticket Validator** | `agents/validator.py` | Input validation & format checking | Raw ticket data | `{is_valid, errors}` | Pre-pipeline validation |
| **Query Analyzer** | `agents/query_analyzer.py` | Query reformulation & keyword extraction | Ticket description | `{reformulation, keywords}` | Improves retrieval queries |
| **Unified Classifier** | `agents/unified_classifier.py` | Category & intent classification | Ticket subject/desc | `{category, confidence, subcategories}` | Filters retrieval scope |
| **Ticket Scorer** | `agents/scorer.py` | Priority & severity scoring | Ticket + classification | `{priority_score, severity}` | Weights in ranking |
| **Query Planner** | `agents/query_planner.py` | Search strategy planning | Analyzed query | `{search_query, search_params}` | Guides retrieval parameters |
| **Response Composer** | `agents/response_composer.py` | Answer generation from context | Context + retrieved docs | `{answer, confidence, actions}` | Generates final response |
| **Evaluator** | `agents/evaluator.py` | Quality & confidence evaluation | Generated response | `{confidence, escalation_flag}` | Quality control gate |
| **Escalation Manager** | `agents/escalation_manager.py` | Escalation logic & routing | Response + evaluation | `{escalate, handler, priority}` | Escalation decision point |
| **Feedback Handler** | `agents/feedback_handler.py` | Feedback processing & learning | Client feedback | `{feedback_processed, metrics_updated}` | Continuous improvement |

---

### Configuration Architecture

```
PipelineConfig (from environment or programmatic)
  ├── EmbeddingConfig
  │   ├── embedder_type: "sentence_transformers" | "haystack"
  │   └── model_name: "all-MiniLM-L6-v2" | "all-mpnet-base-v2"
  │
  ├── VectorStoreConfig
  │   ├── store_type: "in_memory" | "chroma"
  │   ├── collection_name: str
  │   └── persist_dir: Optional[str]
  │
  ├── RetrieverConfig
  │   ├── top_k: int (default 5)
  │   ├── similarity_threshold: float (default 0.4)
  │   ├── similarity_threshold_relaxed: float (default 0.2)
  │   ├── max_results: int (default 10)
  │   └── filters: Dict
  │
  ├── RankerConfig
  │   ├── ranker_type: "semantic" | "keyword" | "hybrid" | "metadata"
  │   ├── semantic_weight: float (for hybrid)
  │   ├── keyword_weight: float (for hybrid)
  │   └── metadata_weight: float (for hybrid)
  │
  ├── ContextConfig
  │   ├── max_tokens: int (default 4000)
  │   ├── chunk_overlap: int (default 100)
  │   ├── merging_strategy: str
  │   ├── target_tokens: int (default 2000)
  │   └── prioritize_similarity: bool
  │
  └── AnswerConfig
      ├── use_context: bool
      ├── min_confidence: float (default 0.5)
      ├── model_id: str (Mistral model)
      └── temperature: float
```

---

## 5. Knowledge Base (KB) System Architecture

The Knowledge Base system manages documentation ingestion, storage, and retrieval:

```
KB System (ai/kb/):
├── kb_manager.py          - Main KB orchestrator (lifecycle management)
├── retriever.py           - Document retrieval with semantic search
├── chunking.py            - Document chunking strategies (recursive, sliding window)
├── config/
│   └── kb_config.py       - KB configuration (chunk size, overlap, etc.)
├── ingest/
│   └── ingest.py          - Document ingestion pipeline
└── storage/
    └── document_store.py  - Document storage backend

Integration Points:
- Vector Store: Stores document embeddings (InMemory, Chroma, FAISS)
- Embeddings: Uses SentenceTransformers for document embeddings
- RAG Pipeline: Feeds retrieved documents to ranking & context stages
```

### KB Configuration

```python
KBConfig:
  chunk_size: 512              # Characters per chunk
  chunk_overlap: 50            # Overlap between chunks
  strategy: "recursive"        # Chunking strategy
  separator: "\n\n"           # Primary separator
  max_documents: 10000        # Document limit
  
IngestConfig:
  supported_formats: [".txt", ".md", ".pdf", ".docx"]
  batch_size: 32
  skip_duplicates: True
  extract_metadata: True
```

---

## 6. Folder Structure & Component Mapping

```
ai/
├── agents/                    # 9 specialized agents
│   ├── validator.py          # Ticket validation
│   ├── scorer.py             # Priority/severity scoring
│   ├── query_analyzer.py     # Query reformulation
│   ├── unified_classifier.py # Category classification
│   ├── query_planner.py      # Search strategy planning
│   ├── response_composer.py  # Answer generation
│   ├── evaluator.py          # Response evaluation
│   ├── escalation_manager.py # Escalation logic
│   └── feedback_handler.py   # Feedback processing
│
├── pipeline/                  # RAG pipeline stages
│   ├── retrieval.py          # VectorRetriever (cosine sim, threshold filtering)
│   ├── ranking.py            # RankerFactory (semantic, keyword, hybrid, metadata)
│   ├── context.py            # ContextOptimizer (token-aware context building)
│   ├── answer.py             # Answer generation with confidence
│   ├── query_intelligence.py # Query analysis & planning
│   ├── orchestrator.py       # Pipeline orchestration
│   └── pipeline_config.py    # Pipeline configuration
│
├── rag/                       # RAG infrastructure
│   ├── embeddings.py         # EmbeddingFactory (SentenceTransformers)
│   ├── vector_store.py       # VectorStoreFactory (InMemory, Chroma, FAISS)
│   └── rag_base.py           # Base RAG classes
│
├── kb/                        # Knowledge Base system
│   ├── kb_manager.py         # KB lifecycle management
│   ├── retriever.py          # Document retrieval
│   ├── chunking.py           # Document chunking
│   ├── config/
│   │   └── kb_config.py      # KB configuration
│   └── ingest/
│       └── ingest.py         # Document ingestion
│
├── app/                       # Application layer
│   ├── main.py               # FastAPI application
│   ├── pipeline.py           # Pipeline client
│   ├── rag.py                # RAG client
│   ├── clients/              # Various client implementations
│   ├── schemas/              # API request/response schemas
│   └── routes/               # API routes
│
├── config/                    # Configuration management
│   └── settings.py           # Settings & environment configuration
│
├── models/                    # Data models
│   └── schemas.py            # Pydantic models (Ticket, Response, etc.)
│
├── utils/                     # Utility functions
│   ├── llm_client.py         # LLM interaction utilities
│   └── metrics.py            # Performance metrics
│
├── data/                      # Data storage
│   ├── metrics/              # Performance metrics data
│   └── tickets/              # Ticket storage
│
└── tests/                     # Test suite
    ├── test_pipeline.py      # Pipeline tests
    ├── test_retrieval.py     # Retrieval tests
    ├── test_agents.py        # Agent tests
    └── test_integration.py   # Integration tests
```

---

### Configuration Architecture

```

---

## 7. Design Patterns Used

1. **Factory Pattern**
   - `EmbeddingFactory`, `VectorStoreFactory`, `RankerFactory`
   - Allows easy switching between implementations

2. **Strategy Pattern**
   - Rankers (Semantic, Keyword, Hybrid, Metadata)
   - Merger strategies (concatenate, summary, structured)
   - Pluggable at runtime

3. **Facade Pattern**
   - `RAGPipeline` hides complexity of 6 stages
   - `SimplifiedRAGPipeline` for simple use cases

4. **Pipeline Pattern**
   - Each stage is independent
   - Clear interfaces between stages
   - Can be reordered or skipped

5. **Configuration Object Pattern**
   - `PipelineConfig` centralizes all settings
   - Environment-based configuration
   - Type-safe (Pydantic dataclasses)

6. **Agent Pattern (Agno Framework)**
   - Each agent is independent with specific responsibilities
   - Agents communicate via data contracts (schemas)
   - LLM-powered decision making using Mistral

---

## 8. Extension Points

1. **Custom Embedders**
   ```python
   class CustomEmbedder(EmbeddingModel):
       def embed_documents(self, texts): ...
       def embed_query(self, text): ...
   ```

2. **Custom Rankers**
   ```python
   class CustomRanker(Ranker):
       def rank(self, documents, query): ...
   ```

3. **Custom Vector Stores**
   ```python
   class CustomVectorStore(VectorStore):
       def add_documents(self, docs, embeddings): ...
       def search(self, embedding, top_k, threshold): ...
   ```

4. **Custom Classifiers**
   - Implement alternative classification logic in agents/
   - Return compatible score format

5. **Custom Context Mergers**
   - Implement alternative context building strategies
   - Extend ContextBuilder base class

---

## 9. Integration with Agents

The RAG pipeline is **fully optional** and works alongside agents:

```python
# Original agent workflow (agents + Mistral LLM)
validation = agent_validator.validate(ticket)
classification = agent_classifier.classify(ticket)
response = agent_composer.generate_response(ticket)

# New RAG workflow (adds retrieval-augmented context)
if classification["category"] in RAG_ENABLED_CATEGORIES:
    context = rag_pipeline.retrieve_context(ticket)
    response = agent_composer.generate_response(ticket, context=context)

# Hybrid (recommended - current implementation)
# Agents use RAG pipeline for context-aware responses
orchestrator = RAGPipeline()
result = orchestrator.process_ticket(ticket)
```

---

## 10. Performance Characteristics

| **Stage** | **Time** | **Notes** |
|----------|---------|---------|
| Validation | 50-100ms | Format & structure checks |
| Query Analysis | 100-150ms | LLM call (Mistral) |
| Classification | 100-150ms | LLM call (Mistral) |
| Embedding Generation | 50-100ms | SentenceTransformers |
| Vector Retrieval | 10-50ms | Cosine similarity O(n) |
| Ranking | 5-20ms | Sorting O(k log k) |
| Context Optimization | 5-10ms | Token counting & merging |
| Answer Generation | 500-1000ms | LLM call (Mistral) |
| Evaluation | 50-100ms | Quality check |
| **Total (Per Ticket)** | **~1-2 seconds** | End-to-end processing |

**Performance Scaling**:
- **Small deployments** (<1000 docs): InMemory vector store ✅
- **Medium deployments** (1k-10k docs): Chroma vector store ✅
- **Large deployments** (>10k docs): FAISS or commercial solutions
- **High throughput** (>100 QPS): Add caching + async processing

**Optimization Opportunities**:
- Cache embeddings for frequently accessed documents
- Implement async retrieval for parallel processing
- Use batch processing for bulk operations
- Monitor and optimize LLM response times

---

## 11. Monitoring & Metrics

Key metrics tracked in `utils/metrics.py` and stored in `data/metrics/`:

### 1. Query Intelligence Metrics
- Validation accuracy rate
- Classification confidence (mean, distribution)
- Query reformulation quality
- Routing effectiveness by category

### 2. Retrieval Metrics
- Average similarity score
- Retrieval success rate
- Fallback triggering frequency
- Document recall rate
- Top-K effectiveness

### 3. Ranking Metrics
- Top-1 relevance score
- Ranking stability (variance)
- Ranker performance by document type
- Score distribution by category

### 4. Context Metrics
- Average tokens used per ticket
- Truncation frequency
- Context efficiency ratio
- Document merge effectiveness

### 5. Answer Generation Metrics
- Confidence score distribution
- Escalation rate by category
- Response time distribution
- User satisfaction (feedback-based)

### 6. System Metrics
- Pipeline throughput (tickets/second)
- End-to-end latency (P50, P95, P99)
- Error rates by stage
- Agent response times

---

## 12. Summary

The RAG pipeline provides:
- ✅ **Complete retrieval-augmented generation workflow** with 6 processing stages
- ✅ **Pluggable, configurable components** via Factory & Strategy patterns
- ✅ **Production-ready error handling** with fallback strategies
- ✅ **Non-breaking integration** with existing Agno agent framework
- ✅ **Clear separation of concerns** across agents, pipeline, RAG, and KB
- ✅ **Extension points for customization** at every stage
- ✅ **Comprehensive monitoring** with metrics tracking at each stage
- ✅ **Agent-based decision making** using Mistral LLM
- ✅ **Knowledge base integration** for document management

**Technologies Used**:
- **LLM**: Mistral AI (via Agno framework)
- **Embeddings**: SentenceTransformers (all-MiniLM-L6-v2 or all-mpnet-base-v2)
- **Vector Stores**: InMemory, Chroma, FAISS-ready
- **Application**: FastAPI with Pydantic validation
- **Orchestration**: RAG Pipeline + Agno Agents
- **Configuration**: Environment-based with type-safe schemas

**Current Status**: 🟢 **Production Ready**
- All components integrated and tested
- Monitoring in place
- Ready for deployment
- Team documentation complete


