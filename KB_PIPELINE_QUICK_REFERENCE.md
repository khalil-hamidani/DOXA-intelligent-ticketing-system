# DOXA KB Pipeline & Agent Architecture - Quick Reference

**Last Updated**: 2025
**Status**: Production-Ready Implementation

---

## 1. System Architecture at a Glance

```
ORCHESTRATOR (10-step deterministic workflow)
    ↓
[Validator] → [Scorer] → [Analyzer] → [Classifier] → [Planner]
    ↓
[Solution Finder] ← ← ← ← ← ← KB PIPELINE (retrieval_interface.py)
    ↓
[Evaluator] → [Composer] → EMAIL TRIGGER → [Orchestrator Signals]
    ↓
[Feedback Handler] → [max 2 retries] → [Escalation Manager]
    ↓
[Continuous Improvement] (learn from escalations)
```

---

## 2. KB Pipeline Modules (ai/kb/)

| Module | Purpose | Key Function | Status |
|--------|---------|--------------|--------|
| **ingest.py** | Parse PDFs, TXT, MD | `ingest_pdf()`, `ingest_directory()` | Existing |
| **chunking.py** | Semantic splitting | `chunk_document()` | New |
| **embeddings.py** | Vector generation | `generate_embeddings()` | Existing |
| **vector_store.py** | Qdrant abstraction | `VectorStoreManager` | New |
| **retrieval_interface.py** | Main API | `retrieve_kb_context()` | New |

---

## 3. The Main Function (retrieve_kb_context)

```python
def retrieve_kb_context(
    query: str,                              # Customer's question
    keywords: List[str],                     # Extracted terms
    category: str,                           # Semantic category
    top_k: int = 5,                          # Results to return
    score_threshold: float = 0.40,           # Min similarity
    kb_confidence_threshold: float = 0.70,   # kb_confident threshold
    max_retrieval_attempts: int = 3,         # Retry limit
    attempt_number: int = 1,                 # Current attempt (1-indexed)
    use_hybrid_search: bool = True           # Semantic + keyword?
) -> Dict:
```

**Returns**:
```python
{
    "results": [
        {
            "chunk_text": str,
            "similarity_score": float,           # 0.0-1.0 cosine similarity
            "metadata": {
                "doc_id": str,
                "section": str,
                "source": str,
                "rank": int
            },
            "ranking_explanation": str
        },
        ...
    ],
    "metadata": {
        "mean_similarity": float,               # Average of results
        "max_similarity": float,                # Highest score
        "min_similarity": float,                # Lowest score
        "chunk_count": int,                     # Number of results
        "retrieval_latency_ms": float,          # Query time
        "kb_confident": bool,                   # SIGNAL: ≥ 0.70?
        "kb_limit_reached": bool,               # SIGNAL: retries exhausted?
        "query_embedding_cached": bool,
        "timestamp": str,
        "suggested_fallback": Optional[str]     # If confidence low
    }
}
```

---

## 4. Critical Signals for Orchestrator

### `kb_confident` (Boolean)

```
True  → mean_similarity ≥ 0.70
        → DECISION: Send satisfaction email NOW (don't wait for feedback)

False → mean_similarity < 0.70
        → DECISION: Request feedback before sending email
```

### `kb_limit_reached` (Boolean)

```
True  → attempt_number ≥ max_retrieval_attempts
        → DECISION: Stop retrying, escalate if needed

False → More retry attempts available
        → DECISION: Can retry with lower threshold
```

---

## 5. Email Trigger Logic

```python
# In orchestrator.py (Step 10)

if solution.get("kb_confident"):
    send_email(subject="Your issue should be resolved")
    # Template: "We found a solution. It should help!"
    # No need to wait for feedback

elif solution.get("kb_limit_reached") and evaluation["escalate"]:
    send_email(subject="Your issue has been escalated")
    # Template: "Specialist will contact you soon"

elif not evaluation["escalate"]:
    send_email(subject="Here's our suggested solution")
    request_feedback(ticket)
    # Template: "Please let us know if this helps"

else:  # escalate
    escalate_ticket(ticket)
    send_email(subject="Your issue is being escalated")
```

---

## 6. Integration Checklist

### Step 1: Create Vector Store (One-time)
```bash
# Start Qdrant
docker run -p 6333:6333 qdrant/qdrant:latest

# Ingest KB documents
python ai/kb/ingest_documents.py
```

### Step 2: Update solution_finder.py
```python
from kb.retrieval_interface import retrieve_kb_context

# OLD: Hard-coded KB_ENTRIES with keyword matching
# NEW: Call retrieve_kb_context()

kb_result = retrieve_kb_context(
    query=ticket.reformulation,
    keywords=ticket.keywords,
    category=ticket.classification.primary_category,
    top_k=5
)

# Extract signals
kb_confident = kb_result["metadata"]["kb_confident"]
kb_limit_reached = kb_result["metadata"]["kb_limit_reached"]
```

### Step 3: Update orchestrator.py
```python
# Pass signals to evaluator
evaluation = evaluate(ticket, solution,
                     kb_confident=solution["kb_confident"],
                     kb_limit_reached=solution["kb_limit_reached"])

# Email decision uses signals
if solution["kb_confident"]:
    send_satisfaction_email()
```

### Step 4: Test End-to-End
```bash
python test_kb_pipeline.py
# Verify: retrieval latency < 300ms
# Verify: kb_confident signal matches mean_similarity
# Verify: email decisions work correctly
```

---

## 7. Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Query latency | < 300ms | Including embedding generation |
| Embedding latency | 50-100ms | Cached on repeat queries |
| Vector search latency | 10-50ms | Qdrant sub-second |
| Mean precision @ threshold | > 70% | Tunable via score_threshold |
| kb_confident accuracy | > 85% | By design (0.70 threshold) |

---

## 8. Configuration (kb/config.py)

```python
class KBConfig:
    # Document ingestion
    chunk_size: int = 512           # Target chunk size in chars
    chunk_overlap: int = 50         # Overlap between chunks
    
    # Embedding
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384
    
    # Vector store
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection_name: str = "doxa_kb"
    
    # Retrieval thresholds
    similarity_threshold: float = 0.40      # Min score for inclusion
    kb_confidence_threshold: float = 0.70   # Threshold for kb_confident flag
    retrieval_attempts_limit: int = 3       # Max retries
    top_k: int = 5                          # Default results to return
```

---

## 9. Troubleshooting

### "No results found"
- Check `mean_similarity` → if 0.0, no chunks matched threshold
- Lower `score_threshold` from 0.40 → 0.30
- Verify KB population: `vs.get_stats()["document_count"]` > 0

### "High latency"
- Check embedding cache hit: `query_embedding_cached` in metadata
- Reduce `top_k` from 5 → 3
- Monitor Qdrant health: `docker logs` for errors

### "Qdrant connection error"
- Verify Qdrant is running: `docker ps | grep qdrant`
- Check host/port: `qdrant_host="localhost"`, `qdrant_port=6333`
- Restart if needed: `docker restart <container_id>`

---

## 10. Key Design Decisions

| Decision | Why | Trade-off |
|----------|-----|-----------|
| Semantic chunking by headers | Preserves document structure | More complex parsing |
| SentenceTransformers | Production-grade, flexible | External dependency |
| Qdrant vector store | Fast, persistent, scalable | Requires external service |
| Cosine similarity | Scale-invariant, well-established | Requires normalized embeddings |
| Hybrid search | Handles semantic + exact matches | ~50ms additional latency |
| Confidence signals (not email) | Non-intrusive, orchestrator decides | Requires orchestrator updates |

---

## 11. File Structure

```
ai/
├── kb/
│   ├── config.py                    # Configuration (existing)
│   ├── ingest.py                    # PDF/TXT/MD parsing (existing)
│   ├── chunking.py                  # Semantic chunking (NEW)
│   ├── embeddings.py                # Vector generation (existing)
│   ├── vector_store.py              # Qdrant abstraction (NEW)
│   ├── retrieval_interface.py       # Main API (NEW)
│   ├── examples.py                  # Usage examples (existing)
│   └── __init__.py
│
├── agents/
│   ├── validator.py                 # (unchanged)
│   ├── scorer.py                    # (unchanged)
│   ├── query_analyzer.py            # Enhanced with entity extraction
│   ├── unified_classifier.py        # NEW: Multi-dimensional classification
│   ├── query_planner.py             # NEW: Query orchestration
│   ├── solution_finder.py           # UPDATED: Call retrieve_kb_context()
│   ├── evaluator.py                 # (unchanged, uses kb signals)
│   ├── response_composer.py         # (unchanged)
│   ├── feedback_handler.py          # (unchanged)
│   ├── escalation_manager.py        # (unchanged)
│   ├── continuous_improvement.py    # (unchanged)
│   └── orchestrator.py              # UPDATED: Email trigger signals
│
└── ...
```

---

## 12. Success Criteria

✅ `retrieve_kb_context()` returns correct structure with signals
✅ Vector search finds relevant documents (> 70% precision)
✅ Confidence signals match similarity scores
✅ Integration requires < 10 lines of code change in solution_finder.py
✅ No modifications to other agents
✅ End-to-end latency < 300ms
✅ Type-safe with full type hints
✅ Production-ready with logging and error handling

---

## 13. Next Phase (Phase 2 CRITICAL)

- [ ] Confidence scoring system (multi-factor)
- [ ] Fallback handling (LLM + heuristic at each stage)
- [ ] Monitoring & metrics (pipeline performance tracking)
- [ ] Skill-based escalation routing
- [ ] Custom exception hierarchy
- [ ] Feedback storage & analysis

---

**Document**: Quick reference for DOXA intelligent ticketing KB pipeline
**Audience**: Engineers, DevOps, Technical leads
**Maintenance**: Update when adding new thresholds, modules, or agents
