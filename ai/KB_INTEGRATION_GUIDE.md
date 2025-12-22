# KB Pipeline Integration Guide

**Quick Integration Steps for DOXA Ticket System**

---

## 1. Quick Start (5 minutes)

### Install Dependencies
```bash
cd ai
pip install -r requirements.txt
```

### Initialize KB
```python
from kb import (
    KBConfig, 
    DocumentIngestor, 
    KnowledgeBaseManager,
    KBRetriever
)

# Setup
config = KBConfig()
kb_manager = KnowledgeBaseManager(config)
ingestor = DocumentIngestor()

# Ingest documents
chunks = ingestor.ingest_directory("path/to/docs")
kb_manager.add_documents(chunks)

# Create retriever
retriever = KBRetriever(kb_manager)
```

### Use in Ticket System
```python
from kb import TicketKBInterface

ticket_kb = TicketKBInterface(retriever)

# In ticket processing
context, results = ticket_kb.get_solution_context(
    ticket_subject=ticket["subject"],
    ticket_description=ticket["description"],
    top_k=5
)

# Use context in RAG for solution generation
```

---

## 2. Integration with Agents

### Modify `solution_finder.py` Agent

```python
# Add to imports
from kb import KBRetriever, KBConfig
from kb.embeddings import KnowledgeBaseManager

class SolutionFinder(Agent):
    def __init__(self):
        # Initialize KB
        self.config = KBConfig()
        self.kb_manager = KnowledgeBaseManager(self.config)
        self.retriever = KBRetriever(self.kb_manager)
    
    def find_solution(self, ticket: Dict) -> str:
        # Get KB context
        kb_context = self.retriever.get_context(
            query=f"{ticket['subject']} {ticket['description']}",
            top_k=5
        )
        
        # Include context in LLM prompt
        prompt = f"""
        Using this knowledge base context:
        {kb_context}
        
        Provide a solution for:
        Subject: {ticket['subject']}
        Description: {ticket['description']}
        """
        
        # Generate solution with LLM
        solution = self.llm.generate(prompt)
        return solution
```

### Add to Orchestrator

```python
# In orchestrator workflow
class Orchestrator:
    def orchestrate(self, ticket):
        # ... existing steps ...
        
        # New step: Get KB context
        kb_context = self.solution_finder.kb_retriever.get_context(
            query=ticket['query'],
            top_k=5
        )
        
        # Pass to solution finder
        solution = self.solution_finder.find_solution(ticket)
        
        # ... rest of workflow ...
```

---

## 3. Configuration for Production

### Environment Variables

```bash
# Vector Database
export KB_VECTOR_DB_TYPE=faiss                    # or qdrant, chroma, pinecone
export KB_VECTOR_DB_PATH=/var/kb/vector_store
export KB_EMBEDDING_DIM=384

# Document Processing
export KB_CHUNK_SIZE=512
export KB_CHUNK_OVERLAP=102
export KB_ENABLE_OCR=true

# Retrieval
export KB_TOP_K=5
export KB_SIMILARITY_THRESHOLD=0.5
export KB_ENABLE_RERANKING=true

# For Qdrant
export KB_QDRANT_HOST=localhost
export KB_QDRANT_PORT=6333

# For Pinecone
export KB_PINECONE_API_KEY=your-key
export KB_PINECONE_INDEX_NAME=doxa-kb
```

### Load Config from Env

```python
from kb.config import load_config_from_env

config = load_config_from_env()
kb_manager = KnowledgeBaseManager(config)
```

---

## 4. Data Preparation

### Organize Documents

```
kb/documents/
├── faq/
│   ├── general.md
│   ├── billing.md
│   └── technical.md
├── guides/
│   ├── user-guide.pdf
│   ├── admin-guide.pdf
│   └── troubleshooting.pdf
└── policies/
    ├── privacy.txt
    └── terms.txt
```

### Ingest All Documents

```python
# One-time setup
from pathlib import Path
from kb.ingest import DocumentIngestor

ingestor = DocumentIngestor(enable_ocr=True)

# Ingest all documents
all_chunks = ingestor.ingest_directory(
    Path("kb/documents/"),
    patterns=["*.pdf", "*.txt", "*.md", "*.html"],
    chunk_size=512,
    chunk_overlap=102,
    use_title_splits=True,
)

# Store in KB
kb_manager.add_documents(all_chunks)

print(f"Ingested {len(all_chunks)} chunks")
```

---

## 5. Search Quality Tuning

### Test Retrieval Quality

```python
# Test queries
test_queries = [
    "How do I reset my password?",
    "What's your refund policy?",
    "I'm getting an error when logging in",
    "How do I export my data?",
    "Can I change my subscription plan?",
]

# Evaluate
for query in test_queries:
    results = retriever.retrieve(query, top_k=5)
    
    if results:
        print(f"Query: {query}")
        print(f"Top Result: {results[0].source_file} ({results[0].similarity_score:.2%})")
        if results[0].similarity_score < 0.5:
            print("⚠️  Low confidence - consider adjusting chunk_size or threshold")
    else:
        print(f"❌ No results for: {query}")
```

### Tune Parameters

```python
# If missing relevant results → lower threshold
config.similarity_threshold = 0.3

# If including irrelevant results → raise threshold
config.similarity_threshold = 0.7

# If results too short → increase chunk_size
config.chunk_size = 1024

# If too slow → reduce chunk_size, disable reranking
config.chunk_size = 256
config.enable_reranking = False

# For higher accuracy → enable all features
config.enable_reranking = True
config.use_score_normalization = True
config.top_k = 10
```

---

## 6. Monitoring & Logging

### Enable Detailed Logging

```python
import logging
from loguru import logger

# Configure loguru
logger.remove()
logger.add(
    "logs/kb.log",
    level="INFO",
    rotation="500 MB",
    format="<level>{level: <8}</level> | {time:YYYY-MM-DD HH:mm:ss} | {message}"
)

# Use in code
logger.info(f"Retrieving results for: {query}")
logger.debug(f"Retrieved {len(results)} chunks with avg score {avg_score}")
```

### Track Metrics

```python
# After retrieval
def track_retrieval_metrics(query, results):
    metrics = {
        "query": query,
        "num_results": len(results),
        "top_score": results[0].similarity_score if results else 0,
        "avg_score": sum(r.similarity_score for r in results) / len(results) if results else 0,
        "timestamp": datetime.now(),
    }
    
    # Log to monitoring system
    logger.info(f"Retrieval: {metrics}")
    
    return metrics
```

---

## 7. Advanced Usage

### Custom Embedding Models

```python
from kb.config import KBConfig, EmbeddingModel

# Use different embedding model
config = KBConfig(
    embedding_model="sentence-transformers/all-mpnet-base-v2"  # More accurate
)
kb_manager = KnowledgeBaseManager(config)
```

### Qdrant for Production

```python
from kb.config import KBConfig, VectorDBType

# Use Qdrant (requires running Qdrant service)
config = KBConfig(
    vector_db_type=VectorDBType.QDRANT,
    qdrant_host="your-qdrant-server",
    qdrant_port=6333,
)
kb_manager = KnowledgeBaseManager(config)
```

### Batch Processing

```python
# Process multiple tickets at once
tickets = [ticket1, ticket2, ticket3, ...]

# Batch retrieval
queries = [f"{t['subject']} {t['description']}" for t in tickets]
batch_results = retriever.batch_retrieve(queries)

# Process results
for ticket, query_results in zip(tickets, batch_results.values()):
    context = retriever.get_context(query=f"{ticket['subject']} {ticket['description']}")
    # Generate solution...
```

---

## 8. Troubleshooting

### Low Retrieval Quality

```python
# 1. Check chunk size
print(f"Chunk size: {config.chunk_size}")
# → Too small might not have enough context
# → Too large might dilute relevance

# 2. Lower similarity threshold
config.similarity_threshold = 0.3  # From default 0.5

# 3. Enable reranking
config.enable_reranking = True

# 4. Increase top_k
config.top_k = 10  # From default 5

# 5. Re-ingest documents with better structure
```

### Memory Issues

```python
# Reduce batch size
kb_manager.embedding_gen.batch_embedding_size = 16  # From 32

# Use smaller embedding model
config.embedding_model = "sentence-transformers/all-MiniLM-L6-v2"

# Use FAISS (not Qdrant)
config.vector_db_type = VectorDBType.FAISS
```

### Slow Retrieval

```python
# Disable reranking
config.enable_reranking = False

# Reduce chunk size
config.chunk_size = 256  # From 512

# Use smaller model
config.embedding_model = "sentence-transformers/all-MiniLM-L6-v2"

# Reduce top_k
config.top_k = 3  # From 5
```

---

## 9. API Reference Summary

### Core Classes

| Class | Purpose |
|-------|---------|
| `KBConfig` | Configuration management |
| `DocumentIngestor` | Document loading & chunking |
| `KnowledgeBaseManager` | KB orchestration |
| `KBRetriever` | Query interface |
| `TicketKBInterface` | Ticket integration |

### Main Methods

```python
# Ingestion
ingestor.ingest_document(file_path)
ingestor.ingest_directory(directory)

# KB Management
kb_manager.add_documents(chunks)
kb_manager.search(query)

# Retrieval
retriever.retrieve(query, top_k, threshold)
retriever.retrieve_by_section(query, section_title)
retriever.retrieve_by_source(query, source_file)
retriever.get_context(query)
retriever.get_related_chunks(chunk_id)
retriever.batch_retrieve(queries)

# Ticket Integration
ticket_kb.get_solution_context(subject, description)
ticket_kb.get_quick_answer(question)
```

---

## 10. Running Examples

```bash
# Run all KB examples
cd ai/kb
python examples.py

# Test individual examples
python -c "from examples import example_1_basic_ingestion; example_1_basic_ingestion()"
```

---

## Checklist for Integration

- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Create KB documents in `ai/kb/documents/`
- [ ] Initialize KB and ingest documents
- [ ] Test retrieval with sample queries
- [ ] Configure chunk_size and threshold for your data
- [ ] Add KB to solution_finder agent
- [ ] Test with sample tickets
- [ ] Monitor retrieval quality in production
- [ ] Set up logging and monitoring
- [ ] Document any custom configurations

---

## Support Resources

- **Documentation**: `KB_IMPLEMENTATION_COMPLETE.md`
- **Examples**: `kb/examples.py`
- **API Reference**: See docstrings in each module
- **Config Reference**: `kb/config.py`

---

**Version**: 1.0.0  
**Status**: Ready for Integration ✅
