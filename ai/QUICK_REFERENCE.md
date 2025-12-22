# QUICK_REFERENCE.md

## RAG Pipeline Quick Reference

### ⚠️ Important: Workstream Separation

**Pipeline Status**: ✅ COMPLETE & READY TO USE

**KB Data Preparation**: 📋 HANDLED BY SEPARATE TEAM
- PDF extraction, OCR, chunking, semantic splitting
- Vector DB setup (ChromaDB, FAISS, Qdrant, Pinecone)
- **See**: [KB_DATA_PREPARATION_WORKSTREAM.md](KB_DATA_PREPARATION_WORKSTREAM.md)

**You Need To Know**:
- Pipeline is ready immediately after KB data arrives
- KB data format: List of chunks with `id`, `content`, `metadata`
- Load KB using: `rag.add_documents(chunks)` or `rag.add_kb_documents(chunks)`
- Integration takes < 1 hour

---

### Installation
No new dependencies required - all are in `requirements.txt`:
```bash
cd ai
pip install -r requirements.txt
```

### Configuration

**Option 1: Environment Variables** (recommended for production)
```bash
export EMBEDDING_TYPE=sentence_transformers
export EMBEDDING_MODEL=all-MiniLM-L6-v2
export VECTOR_STORE_TYPE=in_memory
export RETRIEVER_TOP_K=5
export RANKER_TYPE=hybrid
export CONTEXT_TARGET_TOKENS=2000
export ANSWER_MIN_CONFIDENCE=0.5
```

**Option 2: Programmatic** (for development)
```python
from config.pipeline_config import PipelineConfig

config = PipelineConfig.default()
config.ranker.ranker_type = "semantic"
```

### Basic Usage

**Simplest way** (2-3 lines):
```python
from pipeline.orchestrator import SimplifiedRAGPipeline
from models import Ticket

rag = SimplifiedRAGPipeline()
rag.add_kb_documents([{"id": "1", "category": "technique", "content": "..."}])
answer = rag.answer_ticket(ticket)
```

**Full control**:
```python
from pipeline.orchestrator import RAGPipeline

rag = RAGPipeline()
result = rag.process_ticket(ticket)

# Access each stage:
print(result["stages"]["query_intelligence"])
print(result["stages"]["retrieval"])
print(result["stages"]["ranking"])
print(result["final_response"])
```

### Key Classes

| **Module** | **Class** | **Purpose** |
|-----------|----------|-----------|
| `query_intelligence` | `QueryValidator` | Validate queries |
| `query_intelligence` | `MulticlassClassifier` | Multi-class semantic classification |
| `query_intelligence` | `QueryPlanner` | Route and plan retrieval |
| `rag.embeddings` | `EmbeddingFactory` | Create embedder |
| `rag.vector_store` | `VectorStoreFactory` | Create vector store |
| `retrieval` | `VectorRetriever` | Semantic search |
| `ranking` | `RankingPipeline` | Rank documents |
| `context` | `ContextOptimizer` | Optimize context window |
| `answer` | `AnswerGenerator` | Generate answers |
| `orchestrator` | `RAGPipeline` | Run full pipeline |

### Common Tasks

**Add documents to knowledge base**:
```python
rag.add_documents([
    {
        "id": "doc_1",
        "content": "How to fix crashes",
        "metadata": {"category": "technique"}
    }
])
```

**Process a single ticket**:
```python
result = rag.process_ticket(ticket)
answer = result["final_response"]
```

**Get statistics**:
```python
stats = rag.get_stats()
# {vector_store_size, embedding_dim, ranker_type, store_type, embedding_model}
```

**Change ranker at runtime**:
```python
rag.ranker.reconfigure_ranker("semantic")
```

### Troubleshooting

**Issue**: "No results found"
```python
# Check vector store size
print(rag.get_stats()["vector_store_size"])

# Check retrieval threshold
# Lower it in config
config.retriever.similarity_threshold = 0.2
```

**Issue**: "Embedder not found"
```python
# Check sentence-transformers is installed
pip install sentence-transformers

# Or use Haystack
config.embedding.embedder_type = "haystack"
```

**Issue**: "Low confidence answers"
```python
# Check min_confidence threshold
config.answer.min_confidence = 0.3  # Lower threshold

# Or use different ranker
config.ranker.ranker_type = "semantic"  # Faster, simpler
```

### Performance Tips

1. **Use `in_memory` store** for <10k documents (faster)
2. **Use `all-MiniLM-L6-v2`** embedder (default, 384 dims, fast)
3. **Use `hybrid` ranker** (best quality/speed balance)
4. **Set `CONTEXT_TARGET_TOKENS=2000`** for optimal LLM performance

### Integration with Agents

**Use new pipeline alongside existing agents**:
```python
# Option 1: Original agent pipeline
from agents.orchestrator import process_ticket as agent_process
result1 = agent_process(ticket)

# Option 2: New RAG pipeline
from pipeline.orchestrator import RAGPipeline
rag = RAGPipeline()
result2 = rag.process_ticket(ticket)

# Option 3: Hybrid - use agent validation, then RAG
if validate_ticket(ticket)["valid"]:
    result = rag.process_ticket(ticket)
```

### File Organization

```
ai/
├── pipeline/              # RAG pipeline stages
│   ├── query_intelligence.py    # Query processing
│   ├── retrieval.py             # Vector search
│   ├── ranking.py               # Document ranking
│   ├── context.py               # Context optimization
│   ├── answer.py                # Answer generation
│   └── orchestrator.py           # Complete pipeline
├── rag/                   # Embeddings & vector store
│   ├── embeddings.py            # Embedding models
│   └── vector_store.py          # Vector storage
├── config/
│   ├── settings.py              # API config (existing)
│   └── pipeline_config.py       # Pipeline config (new)
└── agents/                # Your existing agents (unchanged)
```

### Environment Setup for Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install requirements
pip install -r requirements.txt

# Set environment variables
export MISTRAL_API_KEY="your-key"
export EMBEDDING_MODEL="all-MiniLM-L6-v2"
export VECTOR_STORE_TYPE="in_memory"

# Run tests
pytest tests/

# Try it out
python -c "from pipeline.orchestrator import SimplifiedRAGPipeline; print('✓ Pipeline loaded successfully')"
```

### Next Steps

1. Read `PIPELINE_IMPLEMENTATION_GUIDE.md` for detailed documentation
2. Review `IMPLEMENTATION_CHECKLIST.md` for what was implemented
3. Run tests to verify everything works
4. Configure for your use case (embeddings, ranker, context size)
5. Add your KB documents
6. Integrate with agent orchestrator as needed

### Support

For detailed documentation on each component:
- `pipeline/query_intelligence.py` - Query processing
- `rag/embeddings.py` - Embeddings
- `rag/vector_store.py` - Vector storage
- `pipeline/retrieval.py` - Semantic search
- `pipeline/ranking.py` - Ranking strategies
- `pipeline/context.py` - Context optimization
- `pipeline/answer.py` - Answer generation
- `pipeline/orchestrator.py` - Pipeline orchestration

Each file has comprehensive docstrings and type hints.

---

**TL;DR**: The complete RAG pipeline is implemented and ready to use. No breaking changes to existing code. Run `SimplifiedRAGPipeline` for quick usage or `RAGPipeline` for full control.
