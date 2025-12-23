# Knowledge Base (KB) Module

**Production-grade KB ingestion and retrieval pipeline for DOXA ticket system**

## Overview

This module implements a focused, efficient knowledge base system for the DOXA ticket processing system using:

- **PDF-only ingestion** with Mistral OCR for scanned documents
- **Haystack AI** for embeddings with Sentence Transformers
- **Qdrant** vector database with cosine similarity
- **Semantic chunking** with hierarchical organization by ## markdown titles
- **Direct ticket pipeline integration** for context enrichment

## Architecture

```
PDF Documents (input)
         ↓
  Mistral OCR (extract markdown with ## hierarchy)
         ↓
  PDFIngestor (parse sections + semantic chunks)
         ↓
  DocumentChunk objects (with metadata)
         ↓
  HaystackEmbeddingStore (generate embeddings + Qdrant storage)
         ↓
  Cosine Similarity Search (retrieve top-k results)
         ↓
  HaystackRetriever (format + filter results)
         ↓
  TicketKBInterface (integrate with ticket system)
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Key packages:
- `mistralai>=0.0.14` - OCR processing
- `haystack-ai>=1.0.0` - Embeddings + retrieval
- `qdrant-client>=2.7.0` - Vector database
- `sentence-transformers>=2.5.1` - Embedding model

### 2. Start Qdrant

```bash
docker run -p 6333:6333 qdrant/qdrant
```

### 3. Ingest PDFs

```python
from kb.config import KBConfig
from kb.ingest import PDFIngestor
from kb.embeddings import HaystackEmbeddingStore

# Setup
config = KBConfig()
ingestor = PDFIngestor(config)
store = HaystackEmbeddingStore(config)

# Ingest PDFs
chunks = ingestor.ingest_directory("documents/")

# Store in Qdrant
store.add_documents(chunks)
```

### 4. Search KB

```python
from kb.retriever import TicketKBInterface

# Initialize
ticket_kb = TicketKBInterface()

# Get context for ticket
subject = "Installation failed"
description = "Getting error on Windows 10"

context, results = ticket_kb.get_context_for_ticket(subject, description, top_k=5)
print(context)
```

## Module Components

### 1. Config (`kb/config.py`)

Manages all configuration settings.

**Key Classes:**
- `KBConfig` - Main configuration with PDF, chunking, embedding, and Qdrant settings
- `EmbeddingModel` - Enum of supported embedding models

**Environment Variables:**
```
KB_PDF_PATH              # PDF documents directory
KB_MISTRAL_API_KEY       # Mistral API key for OCR
KB_CHUNK_SIZE           # Size of text chunks (default: 512)
KB_CHUNK_OVERLAP        # Overlap between chunks (default: 102)
KB_QDRANT_HOST          # Qdrant server host (default: localhost)
KB_QDRANT_PORT          # Qdrant server port (default: 6333)
KB_QDRANT_COLLECTION    # Qdrant collection name (default: doxa_kb)
KB_TOP_K                # Default number of results (default: 5)
KB_SIMILARITY_THRESHOLD # Minimum similarity score (default: 0.5)
```

### 2. Ingestion (`kb/ingest.py`)

PDF processing with Mistral OCR and semantic chunking.

**Key Classes:**
- `MistralOCRProcessor` - Handles PDF → Markdown extraction with OCR
- `PDFIngestor` - Complete pipeline (extract → parse → chunk)
- `DocumentChunk` - Dataclass representing a text chunk with metadata

**Process:**
1. **PDF → Markdown**: Mistral OCR extracts text, preserves ## hierarchical structure
2. **Parse Sections**: Splits by ## headers into logical sections
3. **Semantic Chunking**: Uses LangChain TextSplitter with overlap
4. **Metadata**: Adds source, section, page, chunk indices

**Example:**
```python
from kb.ingest import PDFIngestor
from kb.config import KBConfig

config = KBConfig()
ingestor = PDFIngestor(config)

chunks = ingestor.ingest_pdf("guide.pdf")
# Returns: [DocumentChunk(...), DocumentChunk(...), ...]

all_chunks = ingestor.ingest_directory("documents/")
# Returns: Combined chunks from all PDFs
```

### 3. Embeddings (`kb/embeddings.py`)

Embedding generation and Qdrant storage.

**Key Classes:**
- `HaystackEmbeddingStore` - Manages embeddings + Qdrant document store

**Features:**
- Uses `SentenceTransformersDocumentEmbedder` for embeddings
- Stores in Qdrant with cosine similarity metric
- Supports batch operations and filtering

**Methods:**
```python
# Add documents to Qdrant
store.add_documents(chunks: List[DocumentChunk]) → int

# Search with similarity
store.search(query: str, top_k: int, threshold: float) → List[Tuple]

# Retrieve document
store.get_document(chunk_id: str) → Optional[Dict]

# Delete documents
store.delete_documents(chunk_ids: List[str]) → int

# Get statistics
store.get_stats() → Dict
```

### 4. Retrieval (`kb/retriever.py`)

Query interface and ticket integration.

**Key Classes:**
- `HaystackRetriever` - Haystack-based retriever with Qdrant backend
- `SearchResult` - Dataclass for search results
- `TicketKBInterface` - High-level interface for ticket system

**HaystackRetriever Methods:**
```python
# Basic search
search(query: str, top_k: Optional[int], threshold: Optional[float]) → List[SearchResult]

# Filtered search
search_by_section(query: str, section_title: str, top_k: Optional[int]) → List[SearchResult]
search_by_source(query: str, source_file: str, top_k: Optional[int]) → List[SearchResult]

# Get context string for LLM prompts
get_context_string(query: str, top_k: Optional[int], include_metadata: bool) → str

# Get statistics
get_kb_stats() → Dict
```

**TicketKBInterface Methods:**
```python
# Get context for ticket processing
get_context_for_ticket(subject: str, description: str, top_k: Optional[int]) 
    → Tuple[str, List[SearchResult]]

# Get best answer from KB
get_answer_from_kb(question: str, top_k: int) → Tuple[Optional[str], float]

# Search FAQ section
search_faq(question: str, top_k: int) → List[Dict]
```

## Configuration Examples

### Default Configuration

```python
from kb.config import KBConfig

config = KBConfig()
# Uses all defaults from environment or hardcoded values
```

### Custom Configuration

```python
from kb.config import KBConfig, EmbeddingModel

config = KBConfig(
    # PDF input
    pdf_input_path="data/knowledge_base/",
    enable_mistral_ocr=True,
    mistral_api_key="sk-...",
    
    # Chunking (larger chunks for more context)
    chunk_size=1024,
    chunk_overlap=256,
    use_title_splits=True,
    
    # Embeddings
    embedding_model=EmbeddingModel.SENTENCE_TRANSFORMERS,
    embedding_dim=384,
    batch_embedding_size=64,
    
    # Qdrant
    qdrant_host="qdrant.example.com",
    qdrant_port=6333,
    qdrant_collection_name="doxa_kb_prod",
    
    # Retrieval
    top_k=10,
    similarity_threshold=0.3,
)
```

### Load from Environment

```python
import os
from kb.config import load_config_from_env

os.environ["KB_PDF_PATH"] = "documents/"
os.environ["KB_MISTRAL_API_KEY"] = "sk-..."
os.environ["KB_QDRANT_HOST"] = "localhost"
os.environ["KB_TOP_K"] = "10"

config = load_config_from_env()
```

## Usage Patterns

### Pattern 1: One-time KB Setup

```python
from kb.config import KBConfig
from kb.ingest import PDFIngestor
from kb.embeddings import HaystackEmbeddingStore

# Setup
config = KBConfig()
ingestor = PDFIngestor(config)
store = HaystackEmbeddingStore(config)

# Ingest all PDFs
chunks = ingestor.ingest_directory("documents/")
print(f"Ingested {len(chunks)} chunks")

# Store in Qdrant
added = store.add_documents(chunks)
print(f"Added {added} documents to Qdrant")

# Done! KB is ready to use
```

### Pattern 2: Search KB

```python
from kb.retriever import HaystackRetriever
from kb.config import KBConfig

config = KBConfig()
retriever = HaystackRetriever(config)

# Simple search
results = retriever.search("How do I install?", top_k=5)

for result in results:
    print(f"{result.similarity_score:.1%} - {result.source_file}")
    print(f"{result.content[:100]}...\n")
```

### Pattern 3: Ticket Context

```python
from kb.retriever import TicketKBInterface

ticket_kb = TicketKBInterface()

# Get context for a ticket
subject = "Service won't start"
description = "Getting timeout error on Linux"

context, results = ticket_kb.get_context_for_ticket(
    subject, 
    description, 
    top_k=5
)

# Use context in ticket response
ticket_response = f"""
Based on our knowledge base:

{context}

Please try the steps above and report back.
"""
```

### Pattern 4: Incremental Updates

```python
from kb.ingest import PDFIngestor
from kb.embeddings import HaystackEmbeddingStore
from kb.config import KBConfig

config = KBConfig()
store = HaystackEmbeddingStore(config)

# Update KB with new PDFs
new_pdf = "documents/latest_guide.pdf"
ingestor = PDFIngestor(config)
chunks = ingestor.ingest_pdf(new_pdf)

# Add to existing KB (Qdrant appends)
added = store.add_documents(chunks)
print(f"Added {added} new chunks to KB")
```

## Document Format

PDFs should have clear structure with markdown headers for organization:

```markdown
# Main Title

## Section 1
Content here...

## Section 2
Content here...

### Subsection 2.1
Detailed content...

### Subsection 2.2
More content...

## Section 3
Final section...
```

**What happens:**
1. Mistral OCR extracts text with ## hierarchy preserved
2. PDFIngestor parses into sections (by ## headers)
3. Each section is split into semantic chunks
4. Chunks are stored with section/title metadata
5. Search returns results grouped by relevance + section

## Performance Characteristics

| Operation | Typical Time | Notes |
|-----------|------------|-------|
| OCR (1 PDF, 10 pages) | 10-30s | Depends on Mistral API latency |
| Embedding generation | 0.5-2s | For ~50 chunks, GPU accelerated |
| Qdrant search (cosine) | <100ms | For typical query, retrieves top-5 |
| Full ingestion (100 PDFs) | 2-5 min | First time, includes OCR |

**Optimization Tips:**
1. Use batch OCR for multiple PDFs
2. Adjust chunk size based on document type (larger for technical docs)
3. Set similarity_threshold appropriately (0.3-0.7 range)
4. Monitor Qdrant memory usage (`get_stats()`)

## Testing

Run integration tests:

```bash
python ai/kb/test_integration.py
```

Tests verify:
- Configuration loading
- DocumentChunk dataclass
- Hierarchical markdown parsing
- Semantic text chunking
- Retriever initialization
- TicketKBInterface creation

## Troubleshooting

### Issue: "Connection refused to Qdrant"
**Solution:** Start Qdrant container
```bash
docker run -p 6333:6333 qdrant/qdrant
```

### Issue: "Mistral API key not found"
**Solution:** Set environment variable
```bash
export KB_MISTRAL_API_KEY="sk-..."
```

### Issue: "Dimension mismatch (384 vs 1536)"
**Solution:** Check embedding model matches config
- Default: Sentence-Transformers (384-dim)
- Mistral Embed: 1280-dim (set `embedding_dim=1280`)

### Issue: "OCR returning garbled text"
**Solution:**
1. Verify PDF is readable (not corrupted)
2. Check Mistral API response status
3. Try text-based PDFs first (avoid scanned images)

### Issue: "Low similarity scores (<0.3)"
**Solution:**
1. Check similarity_threshold setting
2. Verify embeddings are generated correctly
3. Ensure query is specific enough

## Integration with Ticket System

The KB module plugs directly into your ticket processing:

```python
# In your ticket processor
from kb.retriever import TicketKBInterface

ticket_kb = TicketKBInterface()

def enrich_ticket(ticket):
    # Get KB context
    context, chunks = ticket_kb.get_context_for_ticket(
        ticket['subject'],
        ticket['description'],
        top_k=5
    )
    
    # Add to ticket for agent processing
    ticket['kb_context'] = context
    ticket['kb_chunks'] = chunks
    
    return ticket
```

## File Structure

```
kb/
├── __init__.py              # Package exports
├── config.py                # Configuration management
├── ingest.py                # PDF ingestion + chunking
├── embeddings.py            # Haystack + Qdrant embeddings
├── retriever.py             # Query interface + ticket integration
├── test_integration.py       # Integration tests
├── USAGE_EXAMPLE.md         # Usage examples
└── README.md               # This file
```

## Version

**KB Module v2.0.0**
- Focused implementation for DOXA ticket system
- PDF-only with Mistral OCR
- Haystack AI + Qdrant backend
- Direct ticket pipeline integration

## License

Part of DOXA Intelligent Ticketing System
