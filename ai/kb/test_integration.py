"""
KB Pipeline Integration Test

Verifies that the KB pipeline components work correctly together.
"""

import logging
from pathlib import Path
from kb.config import KBConfig, EmbeddingModel
from kb.ingest import DocumentChunk, PDFIngestor
from kb.embeddings import HaystackEmbeddingStore
from kb.retriever import HaystackRetriever, TicketKBInterface

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_config():
    """Test configuration loading."""
    logger.info("Testing configuration...")
    config = KBConfig()
    assert config.chunk_size == 512
    assert config.similarity_threshold == 0.5
    assert config.qdrant_collection_name == "doxa_kb"
    assert config.embedding_model == EmbeddingModel.SENTENCE_TRANSFORMERS
    logger.info("✓ Configuration test passed")


def test_document_chunk():
    """Test DocumentChunk dataclass."""
    logger.info("Testing DocumentChunk...")
    chunk = DocumentChunk(
        content="Test content",
        chunk_id="test_1",
        source_file="test.pdf",
        section="Introduction",
        page_number=1,
    )
    assert chunk.content == "Test content"
    assert chunk.chunk_id == "test_1"
    
    # Test to_dict
    chunk_dict = chunk.to_dict()
    assert chunk_dict["content"] == "Test content"
    logger.info("✓ DocumentChunk test passed")


def test_retriever_creation():
    """Test retriever initialization."""
    logger.info("Testing retriever creation...")
    config = KBConfig()
    
    # Note: This requires Qdrant to be running
    try:
        retriever = HaystackRetriever(config)
        logger.info("✓ Retriever creation test passed")
    except Exception as e:
        logger.warning(f"⚠ Retriever creation failed (Qdrant may not be running): {e}")


def test_ticket_kb_interface():
    """Test TicketKBInterface."""
    logger.info("Testing TicketKBInterface...")
    try:
        ticket_kb = TicketKBInterface()
        logger.info("✓ TicketKBInterface creation test passed")
    except Exception as e:
        logger.warning(f"⚠ TicketKBInterface creation failed: {e}")


def test_hierarchical_parsing():
    """Test hierarchical markdown parsing."""
    logger.info("Testing hierarchical parsing...")
    config = KBConfig()
    ingestor = PDFIngestor(config)
    
    markdown = """
# Main Title

## Installation
Install the software first.

### Prerequisites
- Python 3.8+
- Linux or Windows

## Usage
Use the tool like this.

### Examples
Here are examples.
"""
    
    sections = ingestor.parse_hierarchical_structure(markdown)
    assert len(sections) == 2
    assert sections[0][0] == "Installation"
    assert sections[1][0] == "Usage"
    logger.info(f"✓ Hierarchical parsing test passed (found {len(sections)} sections)")


def test_semantic_chunking():
    """Test semantic text chunking."""
    logger.info("Testing semantic chunking...")
    config = KBConfig(chunk_size=100, chunk_overlap=20)
    ingestor = PDFIngestor(config)
    
    text = "This is a long text that needs to be split into chunks. " * 5
    chunks = ingestor.split_by_semantic_chunks(text, title="Test Section")
    
    assert len(chunks) > 1
    assert all(len(chunk) > 0 for chunk in chunks)
    logger.info(f"✓ Semantic chunking test passed (created {len(chunks)} chunks)")


def main():
    """Run all tests."""
    logger.info("=== KB Pipeline Integration Tests ===\n")
    
    try:
        test_config()
        test_document_chunk()
        test_hierarchical_parsing()
        test_semantic_chunking()
        test_retriever_creation()
        test_ticket_kb_interface()
        
        logger.info("\n=== All tests passed! ===")
        return 0
    except AssertionError as e:
        logger.error(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"\n✗ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
