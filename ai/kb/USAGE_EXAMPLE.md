# KB Pipeline Usage Examples

This document shows how to use the DOXA KB pipeline for ticket system integration.

## Quick Start

### 1. Ingest PDFs with Mistral OCR

```python
from kb.config import KBConfig
from kb.ingest import PDFIngestor
from kb.embeddings import HaystackEmbeddingStore

# Setup
config = KBConfig()
ingestor = PDFIngestor(config)
embedding_store = HaystackEmbeddingStore(config)

# Ingest single PDF
chunks = ingestor.ingest_pdf("documents/installation_guide.pdf")
print(f"Created {len(chunks)} chunks")

# Ingest all PDFs from directory
all_chunks = ingestor.ingest_directory("documents/")
print(f"Total chunks: {len(all_chunks)}")

# Store in Qdrant
added = embedding_store.add_documents(all_chunks)
print(f"Added {added} documents to Qdrant")
```

### 2. Search KB

```python
from kb.retriever import HaystackRetriever

# Initialize retriever
retriever = HaystackRetriever(config)

# Search
query = "How do I install the system?"
results = retriever.search(query, top_k=5)

for result in results:
    print(f"Score: {result.similarity_score:.2%}")
    print(f"Source: {result.source_file}")
    print(f"Content: {result.content[:200]}...")
    print("---")
```

### 3. Get Context for Ticket

```python
from kb.retriever import TicketKBInterface

# Create ticket interface
ticket_kb = TicketKBInterface(config)

# Get context for a ticket
subject = "Installation failed"
description = "Getting error on Windows 10 during setup"

context, results = ticket_kb.get_context_for_ticket(subject, description, top_k=5)

print("=== KB Context for Ticket ===")
print(context)
```

### 4. Get Quick Answer

```python
# Get best answer from KB
question = "What are the system requirements?"
answer, confidence = ticket_kb.get_answer_from_kb(question, top_k=3)

if answer:
    print(f"Answer (confidence: {confidence:.1%}):")
    print(answer)
else:
    print("No matching answer found")
```

## Integration with Ticket Processing

### Example: Enrich Ticket with KB Context

```python
from kb.config import KBConfig
from kb.retriever import TicketKBInterface
from ticket_processing import process_ticket  # Your existing ticket processor

# Initialize KB
ticket_kb = TicketKBInterface(KBConfig())

# Process ticket with KB context
def process_ticket_with_kb(ticket):
    """Add KB context to ticket processing."""
    
    # Get relevant KB context
    context, results = ticket_kb.get_context_for_ticket(
        ticket["subject"],
        ticket["description"],
        top_k=5
    )
    
    # Add context to ticket
    ticket["kb_context"] = context
    ticket["kb_chunks"] = [r.to_dict() for r in results]
    
    # Process with enriched context
    response = process_ticket(ticket)
    return response

# Usage
ticket = {
    "id": "TICKET-123",
    "subject": "Cannot start service",
    "description": "Service fails to start on Linux"
}

result = process_ticket_with_kb(ticket)
print(result)
```

## Configuration

### Custom Configuration

```python
from kb.config import KBConfig, EmbeddingModel

config = KBConfig(
    # PDF processing
    pdf_input_path="data/knowledge_base/",
    enable_mistral_ocr=True,
    mistral_api_key="sk-...",  # From environment or config
    
    # Chunking
    chunk_size=1024,  # Larger chunks
    chunk_overlap=256,
    use_title_splits=True,
    
    # Embeddings
    embedding_model=EmbeddingModel.SENTENCE_TRANSFORMERS,
    embedding_dim=384,
    batch_embedding_size=32,
    
    # Qdrant
    qdrant_host="localhost",
    qdrant_port=6333,
    qdrant_collection_name="doxa_kb",
    
    # Retrieval
    top_k=5,
    similarity_threshold=0.5,
)
```

### Load from Environment

```python
import os
from kb.config import load_config_from_env

# Set environment variables
os.environ["KB_PDF_INPUT_PATH"] = "documents/"
os.environ["KB_MISTRAL_API_KEY"] = "sk-..."
os.environ["KB_QDRANT_HOST"] = "localhost"
os.environ["KB_QDRANT_PORT"] = "6333"

# Load config
config = load_config_from_env()
```

## Advanced Usage

### Search by Section

```python
# Search only in FAQ section
results = retriever.search_by_section(
    "How do I reset my password?",
    section_title="FAQ",
    top_k=3
)
```

### Search by Source

```python
# Search only in specific document
results = retriever.search_by_source(
    "installation error",
    source_file="installation_guide.pdf",
    top_k=5
)
```

### Get Formatted Context

```python
# Get context string with metadata
context = retriever.get_context_string(
    query="How to troubleshoot?",
    top_k=5,
    include_metadata=True
)

# Use in prompt
prompt = f"""
Based on the knowledge base:

{context}

Please help the user with their question.
"""
```

### KB Statistics

```python
# Get KB stats
stats = retriever.get_kb_stats()
print(f"Total documents: {stats['document_count']}")
print(f"Embedding dimension: {stats['embedding_dim']}")
print(f"Collection: {stats['collection']}")
print(f"Similarity metric: {stats['similarity_metric']}")
```

## Document Format

### PDF Structure

PDFs should have clear hierarchical structure using markdown headers:

```
# Main Title

## Section 1
Content here...

## Section 2
Content here...

### Subsection 2.1
Content here...
```

The Mistral OCR processor will:
1. Extract PDF (with OCR for scanned documents)
2. Convert to clean Markdown
3. Preserve hierarchical structure
4. Parse by ## titles for section organization
5. Chunk semantically while respecting section boundaries

### Example PDF Content After OCR

```markdown
# Installation Guide

## Prerequisites
- Python 3.8+
- 4GB RAM
- 1GB disk space

## Installation Steps
1. Download the installer
2. Run the setup
3. Follow prompts
4. Restart system

## Troubleshooting
- If installation fails, check logs
- Ensure all prerequisites are met
```

## Performance Notes

- **First Ingest**: Takes longer (OCR processing), subsequent updates are faster
- **Search Speed**: Qdrant returns results in <100ms for typical queries
- **Memory**: Default config uses ~500MB for Qdrant + embeddings
- **Batch Size**: Adjust `batch_embedding_size` based on available GPU/CPU memory

## Logging

Enable debug logging for troubleshooting:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("kb")
logger.setLevel(logging.DEBUG)

# Now all KB operations will be logged in detail
```

## Docker Deployment

The KB pipeline requires a Qdrant instance:

```bash
# Start Qdrant
docker run -p 6333:6333 qdrant/qdrant

# Then run your KB ingest
python -c "
from kb.config import KBConfig
from kb.ingest import PDFIngestor
from kb.embeddings import HaystackEmbeddingStore

config = KBConfig()
ingestor = PDFIngestor(config)
chunks = ingestor.ingest_directory('documents/')
store = HaystackEmbeddingStore(config)
store.add_documents(chunks)
print('KB initialized successfully')
"
```

## Troubleshooting

### Connection Errors

```
Error: Connection refused to Qdrant
```

**Solution**: Make sure Qdrant is running:
```bash
docker run -p 6333:6333 qdrant/qdrant
```

### OCR Errors

```
Error: Mistral API key not found
```

**Solution**: Set environment variable:
```bash
export KB_MISTRAL_API_KEY="sk-..."
```

### Embedding Dimension Mismatch

```
Error: Dimension mismatch (384 vs 1536)
```

**Solution**: Ensure embedding model dimension matches config. Check `embedding_dim` setting matches model output.

## Support

For issues or questions:
1. Check the logs with `logging.DEBUG` level
2. Verify Qdrant connection: `http://localhost:6333/health`
3. Test OCR separately: `python -c "from kb.ingest import MistralOCRProcessor; ..."`
4. Verify PDF files are readable and not corrupted
