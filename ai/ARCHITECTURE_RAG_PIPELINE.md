# ARCHITECTURE_RAG_PIPELINE.md

## RAG Pipeline Architecture

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

### Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────┐
│              RAGPipeline (Orchestrator)                 │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │ QueryIntelligence Processor                      │   │
│  │  • QueryValidator                                │   │
│  │  • QueryAugmenter (Agent: Agno+Mistral)         │   │
│  │  • MulticlassClassifier (Agent: Agno+Mistral)   │   │
│  │  • QueryPlanner                                  │   │
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
INPUT:
  Ticket {id, client_name, email, subject, description, ...}
  
        ↓
  
STAGE 1 (QueryIntelligence):
  {
    validation: {valid, reasons, signals},
    augmentation: {rephrased, expansion, synonyms, implicit_context},
    summary: str,
    keywords: [str],
    classification: {
      primary_class: str,
      primary_score: float,
      relevant_classes: [str],
      class_scores: {class: {score: float, confidence: float}},
      routing: str
    },
    plan: {
      primary_route: str,
      search_query: str,
      search_params: {top_k, threshold, semantic_classes, ...}
    }
  }
  
        ↓
  
STAGE 2 (Retrieval):
  {
    query: str,
    results: [
      {
        id: str,
        content: str,
        similarity: float,
        metadata: {category, ...}
      }
    ],
    similarity_matrix: [[float]],
    retrieval_info: {total_results, threshold, store_size, ...}
  }
  
        ↓
  
STAGE 3 (Ranking):
  {
    ranked_documents: [
      {
        ...result,
        rank_score: float,
        rank: int
      }
    ],
    ranking_info: {
      count: int,
      ranker: str,
      score_stats: {min, max, mean, std}
    }
  }
  
        ↓
  
STAGE 4 (Context):
  {
    selected_documents: [...],
    context: str,
    token_estimate: int,
    optimization_info: {
      total_documents: int,
      selected_documents: int,
      efficiency: float,
      truncated: bool
    }
  }
  
        ↓
  
STAGE 5 (Answer):
  {
    answer: str,
    confidence: float,
    is_escalation_recommended: bool,
    escalation_reason: str,
    suggested_actions: [str],
    final_response: str (formatted for client)
  }
  
        ↓
  
STAGE 6 (Validation):
  {
    valid: bool,
    issues: [str],
    recommendations: [str],
    confidence: float
  }
  
        ↓
  
OUTPUT:
  final_response: str (ready to send to client)
```

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

### Design Patterns Used

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

---

### Extension Points

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
   - Implement alternative classification logic
   - Return compatible score format

---

### Integration with Agents

The RAG pipeline is **fully optional** and works alongside agents:

```python
# Original agent workflow
result_agent = process_ticket(ticket)

# New RAG workflow
result_rag = rag.process_ticket(ticket)

# Hybrid (recommended)
validation = validate_ticket(ticket)
if validation["valid"]:
    # Use RAG for retrieval
    result = rag.process_ticket(ticket)
else:
    # Agent handles invalid tickets
    result = process_ticket(ticket)
```

---

### Performance Characteristics

| **Stage** | **Time** | **Notes** |
|----------|---------|---------|
| Query Intelligence | 100-300ms | LLM calls (Mistral) |
| Embeddings | 50-100ms | First load cached |
| Vector Retrieval | 10-50ms | O(n) similarity |
| Ranking | 5-20ms | O(k log k) |
| Context | 5-10ms | Greedy selection |
| Answer Generation | 500-1000ms | LLM call (Mistral) |
| **Total** | **~1-2 seconds** | Per ticket |

**Scaling**:
- Suitable for <10k documents (in_memory)
- For >10k: Use Chroma or FAISS
- For high QPS: Add caching layer

---

### Monitoring & Metrics

Key metrics to track:

1. **Query Intelligence**
   - Validation accuracy
   - Classification confidence
   - Routing strategy effectiveness

2. **Retrieval**
   - Avg similarity score
   - Retrieval fallback rate
   - Document recall

3. **Ranking**
   - Top-1 relevance
   - Ranking stability
   - Ranker performance by category

4. **Context**
   - Avg tokens used
   - Truncation rate
   - Context efficiency

5. **Answer**
   - Confidence distribution
   - Escalation rate
   - User satisfaction

---

## Summary

The RAG pipeline provides:
- ✅ Complete retrieval-augmented generation workflow
- ✅ Pluggable, configurable components
- ✅ Production-ready error handling
- ✅ Non-breaking integration with agents
- ✅ Clear separation of concerns
- ✅ Extension points for customization

**Status**: Ready for production deployment.
