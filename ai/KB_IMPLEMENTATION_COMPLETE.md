# Knowledge Base Pipeline - Complete Documentation

## Overview

The Knowledge Base (KB) pipeline is a production-grade ingestion and retrieval system designed for the DOXA Intelligent Ticketing system. It enables semantic search across documents, automatic solution finding, and context-aware ticket resolution.

**Key Features:**
- ✅ Multi-format document ingestion (PDF, TXT, HTML, Markdown)
- ✅ OCR processing for scanned documents
- ✅ Semantic chunking with title-based parent splits
- ✅ Multiple vector database backends (FAISS, Chroma, Qdrant, Pinecone)
- ✅ Advanced retrieval (reranking, score normalization, hybrid search)
- ✅ Ticket system integration
- ✅ Batch processing and statistics

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    DOCUMENT INGESTION LAYER                     │
├─────────────────────────────────────────────────────────────────┤
│  TextLoader  │  PDFLoader  │  HTMLLoader  │  (+ OCR)           │
│                                                                  │
│  ➜ Load & Clean Text                                           │
│  ➜ Extract Sections (by headers)                               │
│  ➜ Semantic Text Splitting                                     │
│  ➜ Generate Chunk Metadata                                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│               EMBEDDING GENERATION LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│  Sentence-Transformers (all-MiniLM-L6-v2)                      │
│                                                                  │
│  ➜ Batch embedding generation                                  │
│  ➜ Configurable models                                         │
│  ➜ Dimension-aware storage                                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              VECTOR DATABASE STORAGE LAYER                       │
├─────────────────────────────────────────────────────────────────┤
│  FAISS  │  Chroma  │  Qdrant  │  Pinecone                      │
│                                                                  │
│  ➜ Store embeddings & metadata                                 │
│  ➜ Maintain chunk-id mappings                                  │
│  ➜ Persist to disk/remote                                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  RETRIEVAL LAYER                                 │
├─────────────────────────────────────────────────────────────────┤
│  KBRetriever (semantic search)                                  │
│                                                                  │
│  ➜ Query embedding generation                                  │
│  ➜ Similarity-based retrieval (top-k)                          │
│  ➜ Result filtering & reranking                                │
│  ➜ Score normalization                                         │
│  ➜ Metadata enrichment                                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              TICKET SYSTEM INTEGRATION LAYER                     │
├─────────────────────────────────────────────────────────────────┤
│  TicketKBInterface                                              │
│                                                                  │
│  ➜ Context generation for tickets                              │
│  ➜ Quick answer extraction                                     │
│  ➜ Solution recommendation                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Module Structure

```
ai/kb/
├── config.py              # Configuration management (KBConfig, VectorDBType)
├── ingest.py             # Document loading & chunking (DocumentIngestor)
├── embeddings.py         # Embedding & vector DB (KnowledgeBaseManager)
├── retriever.py          # Query interface (KBRetriever)
├── examples.py           # Usage examples
├── __init__.py           # Package exports
└── documents/            # Local document storage
```

---

## Configuration

### Basic Configuration

```python
from kb.config import KBConfig, VectorDBType, EmbeddingModel

# Default configuration
config = KBConfig()

# Or with custom settings
config = KBConfig(
    vector_db_type=VectorDBType.CHROMA,
    chunk_size=512,
    chunk_overlap=102,
    top_k=5,
    similarity_threshold=0.5,
    enable_reranking=True,
)
```

### Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `vector_db_type` | FAISS | Vector database (FAISS, CHROMA, QDRANT, PINECONE) |
| `chunk_size` | 512 | Character size of text chunks |
| `chunk_overlap` | 102 | Overlap between chunks |
| `embedding_model` | all-MiniLM-L6-v2 | Sentence-Transformers model |
| `embedding_dim` | 384 | Embedding dimension |
| `top_k` | 5 | Number of results to retrieve |
| `similarity_threshold` | 0.5 | Minimum similarity score |
| `enable_reranking` | True | Use cross-encoder reranking |
| `use_score_normalization` | True | Normalize similarity scores |
| `use_title_splits` | True | Semantic splits by title |

---

## Document Ingestion

### Supported Formats

- **PDF** - With OCR fallback for scanned documents
- **TXT** - Plain text files
- **HTML** - Web pages and HTML documents
- **Markdown** - Markdown files (.md)

### Basic Ingestion

```python
from kb.ingest import DocumentIngestor
from pathlib import Path

ingestor = DocumentIngestor(enable_ocr=True)

# Ingest single document
chunks = ingestor.ingest_document(
    Path("docs/guide.pdf"),
    chunk_size=512,
    chunk_overlap=102,
    use_title_splits=True,
)

# Ingest directory
all_chunks = ingestor.ingest_directory(
    Path("docs/"),
    patterns=["*.pdf", "*.txt", "*.html"],
)
```

### Chunking Strategy

The system uses **semantic chunking** with **title-based parent splits**:

1. **Section Extraction**: Identifies sections by headers (Markdown, HTML, etc.)
2. **Semantic Splitting**: Uses recursive text splitting preserving boundaries
3. **Metadata Generation**: Each chunk stores:
   - Source file path
   - Section title
   - Chunk position
   - Character offsets

---

## Knowledge Base Management

### Initialize KB

```python
from kb.config import KBConfig
from kb.embeddings import KnowledgeBaseManager

config = KBConfig(vector_db_type="faiss")
kb_manager = KnowledgeBaseManager(config)

# Add documents
kb_manager.add_documents(chunks)

# Search
results = kb_manager.search("question here", top_k=5)
```

### Vector Databases

#### FAISS (Default)
- CPU-based similarity search
- Excellent for local deployments
- No external dependencies
- Persistence to disk

```python
from kb.config import VectorDBType

config = KBConfig(vector_db_type=VectorDBType.FAISS)
```

#### Chroma
- Lightweight in-process database
- Great for development
- Automatic persistence
- Built-in similarity search

```python
config = KBConfig(vector_db_type=VectorDBType.CHROMA)
```

#### Qdrant (Production)
- Cloud-ready vector database
- Advanced filtering
- High performance
- Requires running Qdrant service

```python
config = KBConfig(
    vector_db_type=VectorDBType.QDRANT,
    qdrant_host="localhost",
    qdrant_port=6333,
)
```

#### Pinecone (Cloud)
- Fully managed vector database
- Serverless scaling
- Enterprise features

```python
config = KBConfig(
    vector_db_type=VectorDBType.PINECONE,
    pinecone_api_key="your-key",
    pinecone_index_name="doxa-kb",
)
```

---

## Retrieval

### Basic Retrieval

```python
from kb.retriever import KBRetriever

retriever = KBRetriever(kb_manager)

# Simple retrieval
results = retriever.retrieve(
    query="How do I reset my password?",
    top_k=5,
    threshold=0.5,
)

# Process results
for result in results:
    print(f"Chunk: {result.chunk_id}")
    print(f"Relevance: {result.similarity_score:.2%}")
    print(f"Content: {result.content}")
    print(f"Source: {result.source_file}\n")
```

### Advanced Retrieval

```python
# Get combined context
context = retriever.get_context(query, top_k=5)

# Filter by section
results = retriever.retrieve_by_section(query, section_title="FAQ")

# Filter by source file
results = retriever.retrieve_by_source(query, source_file="docs/")

# Get related chunks
related = retriever.get_related_chunks(chunk_id="doc_c1")

# Batch retrieval
queries = ["Q1", "Q2", "Q3"]
results_dict = retriever.batch_retrieve(queries)
```

---

## Ticket System Integration

### Solution Finding for Tickets

```python
from kb.retriever import TicketKBInterface

ticket_kb = TicketKBInterface(retriever)

# Get solution context for ticket
ticket = {
    "subject": "Cannot login",
    "description": "User gets 'Access Denied' error",
}

context, results = ticket_kb.get_solution_context(
    ticket_subject=ticket["subject"],
    ticket_description=ticket["description"],
    top_k=5,
)

# Use context in RAG for solution generation
print(f"Solution Context:\n{context}")
```

### Quick Answers

```python
# Get quick answer to common question
answer = ticket_kb.get_quick_answer(
    question="How do I reset password?",
    top_k=3,
)

if answer:
    print(f"Answer: {answer}")
```

---

## Advanced Features

### Reranking

Uses cross-encoder model to rerank initial results for higher precision:

```python
config = KBConfig(enable_reranking=True)
kb_manager = KnowledgeBaseManager(config)
retriever = KBRetriever(kb_manager)

# Results automatically reranked
results = retriever.retrieve(query)
```

### Score Normalization

Normalizes similarity scores to [0, 1] range for consistent interpretation:

```python
config = KBConfig(use_score_normalization=True)

# Scores normalized automatically
results = retriever.retrieve(query)
for result in results:
    print(f"Score: {result.similarity_score:.2f}")  # Always 0-1
```

### Hybrid Search

Combine semantic and keyword search (future feature):

```python
config = KBConfig(use_hybrid_search=True)
```

---

## Performance Tuning

### Optimize for Speed

```python
config = KBConfig(
    chunk_size=256,           # Smaller chunks = faster search
    embedding_dim=128,        # Lower dimensions
    batch_embedding_size=64,  # Larger batches
    enable_reranking=False,   # Skip reranking if not needed
)
```

### Optimize for Accuracy

```python
config = KBConfig(
    chunk_size=512,            # Larger chunks = more context
    chunk_overlap=256,         # More overlap
    top_k=10,                  # Return more candidates
    similarity_threshold=0.3,  # Lower threshold
    enable_reranking=True,     # Use reranking
)
```

### Memory Usage

- **FAISS**: ~400 bytes per vector (default 384D)
- **Chroma**: Similar to FAISS
- **Qdrant**: Additional disk storage (~1KB per vector with metadata)

### Scaling

- **0-10K chunks**: FAISS or Chroma (single machine)
- **10K-1M chunks**: Qdrant or Pinecone (production)
- **1M+ chunks**: Pinecone with serverless scaling

---

## Error Handling

```python
from kb.config import KBConfig
from kb.embeddings import KnowledgeBaseManager
from kb.retriever import KBRetriever
import logging

# Configure error logging
logging.basicConfig(level=logging.INFO)

try:
    config = KBConfig()
    kb_manager = KnowledgeBaseManager(config)
    retriever = KBRetriever(kb_manager)
    
    results = retriever.retrieve("query")
    
except Exception as e:
    logging.error(f"KB error: {e}")
    # Fallback: return empty results or default answer
    results = []
```

---

## API Reference

### KBConfig
Configuration management class.

**Methods:**
- `get_vector_db_config()` - Get DB-specific config dict

### DocumentIngestor
Main document ingestion engine.

**Methods:**
- `load_document(file_path)` - Load document content
- `clean_text(text)` - Clean and normalize text
- `extract_sections(text)` - Extract sections by headers
- `split_text_semantic(text)` - Semantic text splitting
- `ingest_document(file_path)` - Complete ingestion pipeline
- `ingest_directory(directory)` - Batch ingestion

### KnowledgeBaseManager
KB orchestrator.

**Methods:**
- `add_documents(chunks)` - Add chunks to KB
- `search(query, top_k)` - Search KB

### KBRetriever
Query interface.

**Methods:**
- `retrieve(query, top_k, threshold)` - Retrieve documents
- `retrieve_by_section(query, section_title)` - Filter by section
- `retrieve_by_source(query, source_file)` - Filter by source
- `get_context(query, top_k)` - Get combined context
- `get_related_chunks(chunk_id)` - Get related chunks
- `batch_retrieve(queries)` - Batch retrieval
- `get_kb_stats()` - Get KB statistics

### TicketKBInterface
Ticket system integration.

**Methods:**
- `get_solution_context(subject, description)` - Get solution context
- `get_quick_answer(question)` - Get quick answer

---

## Examples

See `kb/examples.py` for complete working examples:

1. Basic document ingestion
2. KB initialization
3. End-to-end ingestion pipeline
4. Document retrieval
5. Ticket integration
6. Batch retrieval
7. Advanced features

Run examples:
```bash
python ai/kb/examples.py
```

---

## Best Practices

1. **Chunk Size**: Use 256-512 chars for balanced trade-off
2. **Overlap**: Use 10-20% of chunk size (50-100 chars)
3. **Top-K**: Start with 5, increase if missing relevant docs
4. **Threshold**: Use 0.5 for high precision, 0.3 for high recall
5. **Reranking**: Enable for critical use cases (slower but better)
6. **Updates**: Batch document additions for efficiency
7. **Monitoring**: Log retrieval metrics and quality

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Low relevance results | Lower threshold, increase top_k, enable reranking |
| Slow retrieval | Reduce chunk size, disable reranking, use FAISS |
| High memory usage | Reduce batch size, use smaller embedding model |
| Missing documents | Check chunk_overlap, lower similarity_threshold |
| OCR not working | Verify PyPDF2 installed, check PDF quality |

---

## Dependencies

```
chromadb>=0.4.22
sentence-transformers>=2.5.1
qdrant-client>=2.7.0
faiss-cpu>=1.7.0
pinecone-client>=3.0.0
langchain>=0.1.0
PyPDF2>=3.17.0
beautifulsoup4>=4.12.0
```

---

## Future Enhancements

- [ ] Hybrid semantic + keyword search
- [ ] Graph-based retrieval (knowledge graphs)
- [ ] Multi-modal embeddings (text + images)
- [ ] Automatic chunk optimization
- [ ] Distributed processing with Ray
- [ ] Web-based KB management UI
- [ ] A/B testing for retrieval strategies

---

## Support & Feedback

For issues or questions:
1. Check `troubleshooting` section
2. Review examples in `kb/examples.py`
3. Check logs in `loguru` output
4. Report issues with reproduction steps

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Status**: Production Ready ✅
