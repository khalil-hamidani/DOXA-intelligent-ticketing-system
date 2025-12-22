"""
KB Pipeline Example and Integration Guide

Demonstrates how to use the production-grade KB ingestion and retrieval system.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger

from kb.config import KBConfig, VectorDBType, EmbeddingModel, get_default_config
from kb.ingest import DocumentIngestor
from kb.embeddings import KnowledgeBaseManager
from kb.retriever import KBRetriever, TicketKBInterface


def setup_logger():
    """Configure logging."""
    logger.remove()
    logger.add(
        sys.stderr,
        format="<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level="INFO",
    )


def example_1_basic_ingestion():
    """Example 1: Basic document ingestion."""
    print("\n" + "="*80)
    print("EXAMPLE 1: Basic Document Ingestion")
    print("="*80)
    
    # Create ingestion engine
    ingestor = DocumentIngestor(enable_ocr=True)
    
    # Example: Ingest a single file
    sample_file = Path("ai/kb/documents/sample.txt")
    
    # For demo, create a sample document
    sample_file.parent.mkdir(parents=True, exist_ok=True)
    sample_file.write_text("""
    Knowledge Base Sample Document
    
    # Introduction
    This is a sample document for testing the KB ingestion pipeline.
    It demonstrates how to structure documents for optimal chunking.
    
    # Features
    ## Semantic Chunking
    The system uses semantic splitting to create meaningful chunks based on:
    - Title-based parent splits
    - Content boundaries
    - Configurable chunk size and overlap
    
    ## Multiple Formats
    Supports:
    - PDF documents (with OCR for scanned)
    - Plain text files
    - HTML documents
    - Markdown files
    
    # Usage
    Documents are automatically processed and split into chunks.
    Each chunk maintains metadata about its source and position.
    """)
    
    # Ingest the document
    chunks = ingestor.ingest_document(
        sample_file,
        chunk_size=512,
        chunk_overlap=102,
        use_title_splits=True,
    )
    
    print(f"✅ Ingested document: {sample_file.name}")
    print(f"   - Total chunks: {len(chunks)}")
    for i, chunk in enumerate(chunks[:3]):
        print(f"\n   Chunk {i+1}:")
        print(f"   - ID: {chunk.metadata.chunk_id}")
        print(f"   - Section: {chunk.metadata.section_title}")
        print(f"   - Content preview: {chunk.content[:100]}...")


def example_2_kb_initialization():
    """Example 2: Initialize KB with embeddings."""
    print("\n" + "="*80)
    print("EXAMPLE 2: KB Initialization with Embeddings")
    print("="*80)
    
    # Get default config
    config = get_default_config()
    print(f"✅ Configuration:")
    print(f"   - Vector DB: {config.vector_db_type}")
    print(f"   - Embedding Model: {config.embedding_model}")
    print(f"   - Chunk Size: {config.chunk_size}")
    print(f"   - Top-K Results: {config.top_k}")
    
    # Initialize KB manager
    kb_manager = KnowledgeBaseManager(config)
    print(f"\n✅ KB Manager initialized")
    print(f"   - Embedding Dimension: {kb_manager.embedding_gen.embedding_dim}")
    print(f"   - Vector DB Type: {type(kb_manager.vector_db).__name__}")


def example_3_document_ingestion_to_kb():
    """Example 3: Complete ingestion to KB pipeline."""
    print("\n" + "="*80)
    print("EXAMPLE 3: Complete Ingestion to KB Pipeline")
    print("="*80)
    
    # Initialize config and KB
    config = get_default_config()
    kb_manager = KnowledgeBaseManager(config)
    
    # Create ingestor
    ingestor = DocumentIngestor(enable_ocr=True)
    
    # Create sample documents
    doc_dir = Path("ai/kb/documents")
    doc_dir.mkdir(parents=True, exist_ok=True)
    
    docs = {
        "troubleshooting.txt": """
        # Troubleshooting Guide
        
        ## Common Issues
        
        ### Issue: System not responding
        Solution: Check network connection and restart services.
        
        ### Issue: High memory usage
        Solution: Clear cache and reduce batch size.
        """,
        
        "faq.txt": """
        # Frequently Asked Questions
        
        Q: How do I reset my password?
        A: Go to Settings > Security > Change Password
        
        Q: How do I export data?
        A: Use the Export function in the dashboard.
        """,
    }
    
    all_chunks = []
    for filename, content in docs.items():
        file_path = doc_dir / filename
        file_path.write_text(content)
        
        # Ingest document
        chunks = ingestor.ingest_document(file_path)
        all_chunks.extend(chunks)
        print(f"✅ Ingested {filename}: {len(chunks)} chunks")
    
    # Add all chunks to KB
    if all_chunks:
        kb_manager.add_documents(all_chunks)
        print(f"\n✅ Added {len(all_chunks)} chunks to KB")


def example_4_retrieval():
    """Example 4: Retrieve documents from KB."""
    print("\n" + "="*80)
    print("EXAMPLE 4: Document Retrieval")
    print("="*80)
    
    # Initialize KB
    config = get_default_config()
    kb_manager = KnowledgeBaseManager(config)
    
    # Create retriever
    retriever = KBRetriever(kb_manager)
    
    # Example queries
    queries = [
        "How do I reset password?",
        "System is not responding",
        "Export data",
    ]
    
    for query in queries:
        print(f"\n📝 Query: {query}")
        results = retriever.retrieve(query, top_k=3)
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"   Result {i}:")
                print(f"   - Chunk ID: {result.chunk_id}")
                print(f"   - Relevance: {result.similarity_score:.2%}")
                print(f"   - Source: {result.source_file}")
                if result.section_title:
                    print(f"   - Section: {result.section_title}")
        else:
            print("   ❌ No results found")


def example_5_ticket_integration():
    """Example 5: Integration with ticket system."""
    print("\n" + "="*80)
    print("EXAMPLE 5: Ticket System Integration")
    print("="*80)
    
    # Initialize KB and ticket interface
    config = get_default_config()
    kb_manager = KnowledgeBaseManager(config)
    retriever = KBRetriever(kb_manager)
    ticket_kb = TicketKBInterface(retriever)
    
    # Simulate ticket
    ticket = {
        "subject": "Cannot reset password",
        "description": "User is unable to change password through Settings",
    }
    
    print(f"📋 Ticket: {ticket['subject']}")
    
    # Get solution context
    context, results = ticket_kb.get_solution_context(
        ticket["subject"],
        ticket["description"],
        top_k=3,
    )
    
    if results:
        print(f"\n✅ Found {len(results)} relevant documents:")
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result.source_file}")
            if result.section_title:
                print(f"      Section: {result.section_title}")
            print(f"      Confidence: {result.similarity_score:.2%}")
    else:
        print("❌ No relevant documents found in KB")


def example_6_batch_retrieval():
    """Example 6: Batch retrieval for multiple queries."""
    print("\n" + "="*80)
    print("EXAMPLE 6: Batch Retrieval")
    print("="*80)
    
    config = get_default_config()
    kb_manager = KnowledgeBaseManager(config)
    retriever = KBRetriever(kb_manager)
    
    queries = [
        "password reset",
        "data export",
        "system issues",
    ]
    
    results_batch = retriever.batch_retrieve(queries)
    
    print(f"✅ Batch retrieval for {len(queries)} queries:")
    for query, results in results_batch.items():
        print(f"   - '{query}': {len(results)} results")


def example_7_advanced_features():
    """Example 7: Advanced retrieval features."""
    print("\n" + "="*80)
    print("EXAMPLE 7: Advanced Features")
    print("="*80)
    
    config = get_default_config()
    
    # Enable reranking
    config.enable_reranking = True
    config.use_score_normalization = True
    
    kb_manager = KnowledgeBaseManager(config)
    retriever = KBRetriever(kb_manager)
    
    print("✅ Advanced features enabled:")
    print(f"   - Reranking: {config.enable_reranking}")
    print(f"   - Score Normalization: {config.use_score_normalization}")
    
    # Get KB statistics
    stats = retriever.get_kb_stats()
    print(f"\n📊 KB Statistics:")
    for key, value in stats.items():
        print(f"   - {key}: {value}")


def main():
    """Run all examples."""
    setup_logger()
    
    print("\n" + "="*80)
    print("KNOWLEDGE BASE PIPELINE - EXAMPLES AND INTEGRATION GUIDE")
    print("="*80)
    
    try:
        example_1_basic_ingestion()
        example_2_kb_initialization()
        example_3_document_ingestion_to_kb()
        example_4_retrieval()
        example_5_ticket_integration()
        example_6_batch_retrieval()
        example_7_advanced_features()
        
        print("\n" + "="*80)
        print("✅ ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("="*80)
        
    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)
        print(f"\n❌ ERROR: {e}")


if __name__ == "__main__":
    main()
