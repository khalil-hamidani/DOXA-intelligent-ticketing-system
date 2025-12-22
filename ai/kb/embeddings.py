"""
Haystack AI Embedding and Qdrant Vector Database Module

Handles embedding generation using Haystack AI and storage in Qdrant vector database.
Uses cosine similarity for document retrieval.
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

try:
    from haystack import Document, Pipeline
    from haystack.document_stores.qdrant import QdrantDocumentStore
    from haystack.components.embedders import SentenceTransformersDocumentEmbedder, SentenceTransformersQueryEmbedder
    from haystack.components.retrievers.document_finders import qdrant_similarity_retriever
except ImportError:
    raise ImportError("haystack-ai package required. Install: pip install haystack-ai")

try:
    from qdrant_client import QdrantClient
except ImportError:
    raise ImportError("qdrant-client required. Install: pip install qdrant-client")

from kb.ingest import DocumentChunk
from kb.config import KBConfig

logger = logging.getLogger(__name__)


class HaystackEmbeddingStore:
    """Manages embeddings and storage using Haystack AI + Qdrant."""
    
    def __init__(self, config: KBConfig):
        """
        Initialize Haystack embedding store with Qdrant backend.
        
        Args:
            config: KBConfig instance with Qdrant settings
        """
        self.config = config
        logger.info(f"Initializing Haystack + Qdrant with collection: {config.qdrant_collection_name}")
        
        # Initialize Qdrant document store (in-memory or connect to remote)
        self.doc_store = QdrantDocumentStore(
            url=f"http://{config.qdrant_host}:{config.qdrant_port}",
            index=config.qdrant_collection_name,
            embedding_dim=config.embedding_dim,
            similarity="cosine",  # Use cosine similarity as specified
            recreate_index=False,
        )
        
        # Initialize embedders
        self.doc_embedder = SentenceTransformersDocumentEmbedder(
            model=str(config.embedding_model),
            batch_size=config.batch_embedding_size,
        )
        
        self.query_embedder = SentenceTransformersQueryEmbedder(
            model=str(config.embedding_model),
        )
    
    def add_documents(self, chunks: List[DocumentChunk]) -> int:
        """
        Add document chunks to Qdrant with embeddings.
        
        Args:
            chunks: List of DocumentChunk objects
        
        Returns:
            Number of documents added
        """
        if not chunks:
            logger.warning("No chunks to add")
            return 0
        
        logger.info(f"Adding {len(chunks)} chunks to Qdrant")
        
        # Convert DocumentChunk objects to Haystack Document objects
        documents = []
        for chunk in chunks:
            doc = Document(
                content=chunk.content,
                meta={
                    "chunk_id": chunk.chunk_id,
                    "source_file": chunk.source_file,
                    "title": chunk.title,
                    "section": chunk.section,
                    "page_number": chunk.page_number,
                    "chunk_index": chunk.chunk_index,
                    "total_chunks": chunk.total_chunks,
                }
            )
            documents.append(doc)
        
        # Generate embeddings for all documents
        logger.info(f"Generating embeddings for {len(documents)} documents")
        embedded_docs = self.doc_embedder.run(documents=documents)["documents"]
        
        # Write to Qdrant
        self.doc_store.write_documents(embedded_docs)
        
        logger.info(f"Successfully added {len(embedded_docs)} documents to Qdrant")
        
        return len(embedded_docs)
    
    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Search for similar documents using cosine similarity.
        
        Args:
            query: Search query
            top_k: Number of results (uses config if not provided)
            threshold: Minimum similarity threshold (uses config if not provided)
        
        Returns:
            List of (chunk_id, similarity_score, metadata) tuples
        """
        top_k = top_k or self.config.top_k
        threshold = threshold if threshold is not None else self.config.similarity_threshold
        
        logger.info(f"Searching for: {query} (top_k={top_k}, threshold={threshold})")
        
        # Generate query embedding
        query_embedding = self.query_embedder.run(query=query)["query_embedding"]
        
        # Perform similarity search in Qdrant
        # Using cosine similarity (built-in to Qdrant config)
        results = self.doc_store.query(
            query_embedding=query_embedding,
            top_k=top_k,
            similarity_threshold=threshold,
            return_embedding=False,
        )
        
        # Format results
        formatted_results = []
        for doc in results:
            similarity_score = doc.score  # Cosine similarity from Qdrant
            chunk_id = doc.meta.get("chunk_id", "unknown")
            metadata = doc.meta
            
            if similarity_score >= threshold:
                formatted_results.append((chunk_id, similarity_score, metadata))
        
        logger.info(f"Found {len(formatted_results)} results with similarity >= {threshold}")
        
        return formatted_results
    
    def get_document(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document by chunk ID.
        
        Args:
            chunk_id: Document chunk ID
        
        Returns:
            Document dict with content and metadata or None
        """
        try:
            # Query Qdrant by metadata
            results = self.doc_store.query_by_meta(meta={"chunk_id": chunk_id}, limit=1)
            
            if results:
                doc = results[0]
                return {
                    "chunk_id": chunk_id,
                    "content": doc.content,
                    "metadata": doc.meta,
                }
        except Exception as e:
            logger.warning(f"Error retrieving document {chunk_id}: {e}")
        
        return None
    
    def delete_documents(self, chunk_ids: List[str]) -> int:
        """
        Delete documents by chunk IDs.
        
        Args:
            chunk_ids: List of chunk IDs to delete
        
        Returns:
            Number of documents deleted
        """
        deleted_count = 0
        for chunk_id in chunk_ids:
            try:
                # Delete by metadata filter
                self.doc_store.delete_documents(filters={
                    "field": "meta.chunk_id",
                    "operator": "==",
                    "value": chunk_id,
                })
                deleted_count += 1
            except Exception as e:
                logger.warning(f"Error deleting {chunk_id}: {e}")
        
        logger.info(f"Deleted {deleted_count} documents from Qdrant")
        
        return deleted_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        try:
            stats = {
                "collection": self.config.qdrant_collection_name,
                "embedding_dim": self.config.embedding_dim,
                "similarity_metric": "cosine",
                "document_count": len(self.doc_store),
            }
            return stats
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
