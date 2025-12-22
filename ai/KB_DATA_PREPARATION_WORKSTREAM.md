# KB Data Preparation Workstream

**Status**: 📋 Pending (Separate Team Responsibility)  
**Owner**: Another Team Member  
**Related to**: RAG Pipeline (which is ✅ COMPLETE)  
**Dependency**: This workstream prepares data FOR the pipeline

---

## Overview

The **RAG Pipeline is complete and ready to consume data**. The **KB Data Preparation** is a separate, independent workstream handled by another team member. This document outlines that scope.

**Clear Division of Responsibilities:**
- ✅ **Our Pipeline** (COMPLETE): Processes tickets + retrieves from KB
- 📋 **Their Data Prep** (PENDING): Prepares KB data for storage

---

## Workstream Scope

### 1. PDF/Document Parsing & OCR
**Goal**: Convert unstructured documents to structured, text-accessible format

**Technologies**:
- **Mistral OCR**: `docs.mistral.ai/capabilities/documents_ai/basic_ocr`
- **Input Formats**: PDF, images (scanned documents)
- **Output Format**: Text, JSON, HTML (structured)
- **Key Task**: Extract text from scanned PDFs using Mistral's OCR capabilities

**Deliverable**: 
```json
{
  "document_id": "doc_001",
  "source_type": "pdf",
  "content": "Extracted text content from document...",
  "metadata": {
    "pages": 5,
    "language": "fr",
    "extracted_date": "2025-12-22"
  }
}
```

---

### 2. Text Chunking & Semantic Splitting
**Goal**: Break documents into optimal chunks for semantic search

**Technologies**:
- **LangChain Text Splitter**: Semantic chunking capabilities
- **Split Strategy**: 
  - Primary: Split by section titles (## markdown headers)
  - Secondary: Parent-child hierarchical splits
  - Configure: chunk size, overlap, boundaries
- **Overlap**: Configurable (10-20% recommended for context preservation)

**Deliverable**: Array of chunks with metadata
```python
[
  {
    "id": "chunk_001",
    "parent_id": "doc_001",
    "content": "Chunk 1 text content...",
    "metadata": {
      "section": "Installation",
      "chunk_size": 256,
      "position": 1
    }
  },
  {
    "id": "chunk_002",
    "parent_id": "doc_001",
    "content": "Chunk 2 text content...",
    "metadata": {
      "section": "Installation",
      "chunk_size": 250,
      "position": 2
    }
  }
]
```

---

### 3. Embeddings Generation
**Goal**: Convert text chunks to numerical vectors for similarity search

**Technologies**:
- **Sentence-Transformers** (handled by pipeline): `all-MiniLM-L6-v2` or `all-mpnet-base-v2`
- **Embedding Dimension**: 384 or 768 dims (model-dependent)
- **Input**: Text chunks from step 2
- **Output**: Numerical vectors (floating-point arrays)

**Note**: Our pipeline **automatically handles embeddings generation** when you add documents. No manual work needed here—just pass chunks from step 2 to the pipeline's `add_documents()` method.

**Integration Point**:
```python
from pipeline.orchestrator import RAGPipeline

rag = RAGPipeline()
rag.add_documents(chunks_from_step_2)
# Embeddings generated automatically
```

---

### 4. Vector Database Storage
**Goal**: Persist embeddings for fast similarity search

**Technology Options** (choose one or combine):
- **ChromaDB**: Lightweight, in-process, JSON persistence
- **FAISS**: Facebook's similarity search (in-memory, fast)
- **Qdrant**: Dedicated vector DB, REST API, production-grade
- **Pinecone**: Managed service, cloud-based, serverless

**Our Pipeline Supports**:
- ✅ **In-Memory Vector Store** (default, good for dev/test)
- ✅ **ChromaDB** (default for persistence, lightweight)
- 🔧 **Extensible**: Can add FAISS, Qdrant, Pinecone via `VectorStoreFactory`

**Integration Point**:
```python
from config.pipeline_config import PipelineConfig

# ChromaDB (recommended for data prep phase)
config = PipelineConfig(
    vector_store_type="chroma",
    vector_store_collection="kb",
    vector_store_persist_dir="./chromadb"
)
rag = RAGPipeline(config)
rag.add_documents(chunks)  # Stored in ChromaDB
```

---

### 5. Query Similarity & Retrieval
**Goal**: Enable semantic similarity-based document matching

**Technologies**:
- **Haystack AI**: `QdrantEmbeddingRetriever` for similarity search
- **Similarity Metric**: Cosine similarity (default in our pipeline)
- **Retrieval Method**: Top-k document matching

**Our Pipeline Handles Retrieval**:
- ✅ Automatically computes cosine similarity
- ✅ Filters by threshold (default 0.4)
- ✅ Falls back to relaxed threshold (0.2) if needed
- ✅ Returns top-k results with scores

**No Manual Work Needed**: The pipeline's `retrieval.py` module handles all similarity matching.

**Integration Point**:
```python
# User queries ticket → Pipeline retrieves relevant documents
ticket = Ticket(id="t1", subject="App crashes...")
result = rag.process_ticket(ticket)
# Retrieval stage automatically executes
print(result["stages"]["retrieval"]["results"])  # Retrieved documents with scores
```

---

## Workstream Phases

### Phase 1: Document Preparation (Weeks 1-2)
- [ ] Identify all source documents (PDFs, text files, etc.)
- [ ] Extract text using Mistral OCR (for scanned PDFs)
- [ ] Standardize formats to text/JSON/HTML
- [ ] Validate extraction quality

**Input**: Source documents  
**Output**: Extracted, cleaned text content

---

### Phase 2: Chunking & Structuring (Weeks 2-3)
- [ ] Define chunk size (recommended: 256-512 tokens)
- [ ] Configure overlap (recommended: 10-20%)
- [ ] Identify section boundaries (## headers)
- [ ] Implement LangChain semantic splitter
- [ ] Apply chunking to all documents
- [ ] Add metadata (section, category, source)

**Input**: Extracted text from Phase 1  
**Output**: Chunks with metadata, organized for storage

---

### Phase 3: Vector DB Setup (Week 3)
- [ ] Choose vector DB (recommend ChromaDB for phase 1)
- [ ] Configure storage backend
- [ ] Set up connection parameters
- [ ] Create collection schema
- [ ] Test persistence & retrieval

**Input**: Chunks with metadata from Phase 2  
**Output**: Configured vector DB ready for embeddings

---

### Phase 4: Data Loading (Week 4)
- [ ] Load chunks into pipeline's `add_documents()` method
- [ ] Embeddings automatically generated
- [ ] Verify storage in vector DB
- [ ] Test similarity queries
- [ ] Document final KB statistics

**Input**: Prepared chunks, configured vector DB  
**Output**: KB fully loaded, indexed, searchable

---

## Integration with Pipeline

### How Pipeline Consumes KB Data

**Step 1**: Your team prepares chunks
```python
chunks = [
  {"id": "c1", "content": "...", "metadata": {...}},
  {"id": "c2", "content": "...", "metadata": {...}},
]
```

**Step 2**: Our pipeline loads chunks
```python
from pipeline.orchestrator import RAGPipeline
from config.pipeline_config import PipelineConfig

# Configure for your vector DB choice
config = PipelineConfig(
    vector_store_type="chroma",  # or "in_memory"
    embedding_model="all-MiniLM-L6-v2"
)
rag = RAGPipeline(config)

# Load KB data
rag.add_documents(chunks)
```

**Step 3**: Pipeline is ready to answer tickets
```python
ticket = Ticket(...)
result = rag.process_ticket(ticket)
# Full 6-stage pipeline executes automatically
```

**No additional work needed**: Embeddings, retrieval, ranking, context, and answer generation are all automatic.

---

## Key Configuration Parameters

### For Your Data Prep Phase

**Chunking**:
- `chunk_size`: 256-512 tokens (adjust based on content)
- `chunk_overlap`: 50-100 tokens (preserve context)
- `split_by`: `##` headers (semantic boundaries)

**Metadata** (add to each chunk):
```python
{
  "id": "unique_chunk_id",
  "category": "technique|facturation|authentification|autre",
  "section": "Installation|Troubleshooting|etc",
  "source": "manual_kb|help_docs|faq",
  "priority": "high|medium|low"  # Optional
}
```

**Vector DB** (recommend for Phase 1):
- **Store**: ChromaDB (lightweight, easy to set up)
- **Collection Name**: "kb" (configurable)
- **Persist Dir**: `./chromadb/` (for data preservation)

---

## Handoff Checklist

### From Your Team → To Our Pipeline

- [ ] Documents extracted and text-accessible
- [ ] Documents chunked with appropriate size/overlap
- [ ] Metadata added (category, section, source)
- [ ] Chunks formatted as:
  ```python
  [
    {
      "id": "chunk_id",
      "content": "text...",
      "metadata": {
        "category": "...",
        "section": "...",
        "source": "..."
      }
    }
  ]
  ```
- [ ] Vector DB configured (ChromaDB recommended)
- [ ] Connection parameters documented
- [ ] Test chunks loaded successfully

### What Our Pipeline Will Do Automatically

- ✅ Generate embeddings using configured model
- ✅ Store embeddings in vector DB
- ✅ Create similarity index
- ✅ Enable semantic search
- ✅ Retrieve relevant documents for queries
- ✅ Rank results using configurable rankers
- ✅ Optimize context for LLM
- ✅ Generate answers with context

---

## Reference Documentation

**For Your Team**:
- [Mistral OCR Docs](https://docs.mistral.ai/capabilities/documents_ai/basic_ocr)
- [LangChain Text Splitter](https://python.langchain.com/docs/modules/data_connection/document_loaders)
- [ChromaDB Docs](https://docs.trychroma.com/)
- [Qdrant Docs](https://qdrant.tech/documentation/) (if choosing Qdrant)
- [Pinecone Docs](https://docs.pinecone.io/) (if choosing Pinecone)

**For Integration**:
- [RAG Pipeline - add_documents() API](PIPELINE_IMPLEMENTATION_GUIDE.md#adding-documents)
- [Configuration Guide](QUICK_REFERENCE.md#configuration)
- [Integration Examples](README_RAG_PIPELINE.md#integration-with-existing-code)

---

## Dependencies & Compatibility

### Required (for data prep):
- `mistral-client` (for OCR)
- `langchain` (for semantic chunking)
- `chromadb` (for vector storage, or alternative)

### Our Pipeline Provides:
- `sentence-transformers` (embeddings)
- `numpy` (vector operations)
- `pydantic` (data validation)

### No Conflicts:
- These are independent workstreams
- Data prep and pipeline can work in parallel
- Once chunks are ready, pipeline integration takes < 1 hour

---

## Timeline

| Week | Data Prep Team | Pipeline Team |
|------|----------------|---------------|
| Week 1 | PDF extraction & OCR | ✅ COMPLETE |
| Week 2 | Chunking & metadata | ✅ COMPLETE |
| Week 3 | Vector DB setup | ✅ COMPLETE |
| Week 4 | Data loading & testing | Integration testing |
| Week 5 | KB validation | Pilot deployment |
| Week 6 | KB optimization | Production deployment |

---

## Support & Questions

### For Data Preparation Issues:
- Refer to technology documentation (Mistral, LangChain, ChromaDB, etc.)
- Contact your data prep team lead

### For Pipeline Integration Issues:
- Review [PIPELINE_IMPLEMENTATION_GUIDE.md](PIPELINE_IMPLEMENTATION_GUIDE.md)
- Check [QUICK_REFERENCE.md](QUICK_REFERENCE.md#troubleshooting)
- See examples in [README_RAG_PIPELINE.md](README_RAG_PIPELINE.md)

### For Architecture Questions:
- See [ARCHITECTURE_RAG_PIPELINE.md](ARCHITECTURE_RAG_PIPELINE.md)
- Review component diagrams and data flow

---

## Summary

**Your Responsibility** (Data Prep Team):
1. Extract text from PDFs using Mistral OCR
2. Chunk documents with LangChain semantic splitter
3. Add metadata (category, section, source)
4. Set up vector DB (ChromaDB recommended)
5. Load chunks into pipeline

**Our Responsibility** (Pipeline Team):
1. ✅ COMPLETE: Build RAG pipeline
2. ✅ COMPLETE: Handle embeddings
3. ✅ COMPLETE: Manage vector storage & retrieval
4. ✅ COMPLETE: Rank results
5. ✅ COMPLETE: Optimize context
6. ✅ COMPLETE: Generate answers

**Result**: Complete, production-ready system without bottlenecks.

---

**This document serves as the clear boundary between the two workstreams. Both can proceed independently and integrate seamlessly in Week 4.**
