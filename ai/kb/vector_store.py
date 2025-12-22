"""
Vector Store Abstraction Layer: Qdrant Vector Database

Provides clean interface for:
1. Storing document embeddings in Qdrant
2. Searching by similarity
3. Updating/deleting documents
4. Health checks and monitoring

Abstracts Qdrant complexity, allows future swapping to Weaviate/Pinecone.

Production-ready with error handling and connection pooling.
"""

import logging
from typing import List, Dict, Optional, Any, Tuple
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

# Connection pool cache
_qdrant_client_cache = None


@dataclass
class VectorDocument:
    """Document with metadata stored in vector store."""
    doc_id: str
    chunk_text: str
    embedding: np.ndarray  # Vector (384-dim for all-MiniLM-L6-v2)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Auto-populated
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict:
        """Convert to dict for Qdrant storage."""
        return {
            "doc_id": self.doc_id,
            "chunk_text": self.chunk_text,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            # Embedding stored separately in Qdrant
        }


class VectorStoreManager:
    """
    Abstraction layer for vector database operations.
    
    Handles:
    - Connection management
    - CRUD operations
    - Search/similarity
    - Index management
    - Monitoring
    
    Can be swapped for Weaviate, Pinecone, etc. without changing calling code.
    """
    
    def __init__(
        self,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        collection_name: str = "doxa_kb",
        embedding_dim: int = 384,
        recreate_index: bool = False
    ):
        """
        Initialize vector store connection.
        
        Args:
            qdrant_host: Qdrant server hostname
            qdrant_port: Qdrant server port
            collection_name: Collection name in Qdrant
            embedding_dim: Dimension of embeddings (384 for all-MiniLM-L6-v2)
            recreate_index: If True, delete and recreate collection
        """
        
        self.qdrant_host = qdrant_host
        self.qdrant_port = qdrant_port
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim
        
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
            
            global _qdrant_client_cache
            
            # Use cached client if available
            if _qdrant_client_cache is not None:
                self.client = _qdrant_client_cache
                logger.info("Using cached Qdrant client")
            else:
                # Initialize new client
                logger.info(f"Connecting to Qdrant at {qdrant_host}:{qdrant_port}")
                self.client = QdrantClient(host=qdrant_host, port=qdrant_port)
                _qdrant_client_cache = self.client
            
            # Get or create collection
            try:
                collections = self.client.get_collections()
                collection_exists = any(c.name == collection_name for c in collections.collections)
                
                if collection_exists and recreate_index:
                    logger.info(f"Deleting existing collection: {collection_name}")
                    self.client.delete_collection(collection_name)
                    collection_exists = False
                
                if not collection_exists:
                    logger.info(f"Creating collection: {collection_name}")
                    self.client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(
                            size=embedding_dim,
                            distance=Distance.COSINE
                        )
                    )
            
            except Exception as e:
                logger.error(f"Failed to manage collection: {e}")
                raise
        
        except ImportError:
            logger.error("qdrant-client not installed. Install with: pip install qdrant-client")
            raise
    
    def add_documents(
        self,
        documents: List[VectorDocument],
        batch_size: int = 100
    ) -> Dict[str, int]:
        """
        Add documents to vector store.
        
        Args:
            documents: List of VectorDocument objects
            batch_size: Process in batches for efficiency
        
        Returns:
            Dict with keys:
            - "added": Number of documents added
            - "failed": Number of failed additions
            - "errors": List of error messages (if any)
        
        Example:
            docs = [
                VectorDocument(
                    doc_id="doc_1_chunk_0",
                    chunk_text="How to reset password...",
                    embedding=np.array([...]),
                    metadata={"source": "faq.pdf", "section": "Authentication"}
                ),
                ...
            ]
            result = vs_manager.add_documents(docs)
            # Returns: {"added": 142, "failed": 0, "errors": []}
        """
        
        if not documents:
            return {"added": 0, "failed": 0}
        
        added = 0
        failed = 0
        errors = []
        
        try:
            from qdrant_client.models import PointStruct
            
            # Process in batches
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                
                try:
                    # Prepare points for Qdrant
                    points = []
                    for idx, doc in enumerate(batch):
                        point_id = _doc_id_to_point_id(doc.doc_id)
                        
                        points.append(PointStruct(
                            id=point_id,
                            vector=doc.embedding.tolist(),
                            payload={
                                "doc_id": doc.doc_id,
                                "chunk_text": doc.chunk_text,
                                "metadata": doc.metadata,
                                "timestamp": doc.timestamp
                            }
                        ))
                    
                    # Upsert to Qdrant (insert or update)
                    self.client.upsert(
                        collection_name=self.collection_name,
                        points=points
                    )
                    
                    added += len(batch)
                    logger.debug(f"Added batch of {len(batch)} documents")
                
                except Exception as e:
                    failed += len(batch)
                    error_msg = f"Batch addition failed: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
        
        except Exception as e:
            logger.exception(f"Failed to add documents: {e}")
            failed += len(documents) - added
            errors.append(str(e))
        
        result = {
            "added": added,
            "failed": failed,
            "errors": errors if errors else []
        }
        
        logger.info(f"Document addition summary: {result}")
        return result
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        threshold: float = 0.40,
        category_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        Search for similar documents by embedding.
        
        Args:
            query_embedding: Query vector (np.ndarray)
            top_k: Number of results to return
            threshold: Minimum similarity score (0.0-1.0)
            category_filter: Optional filter by metadata category
        
        Returns:
            List of results with structure:
            [
                {
                    "chunk_text": str,
                    "similarity_score": float (0.0-1.0),
                    "doc_id": str,
                    "section": str,
                    "source": str,
                    "metadata": dict
                },
                ...
            ]
        
        Example:
            from kb.embeddings import generate_embeddings
            query_emb = generate_embeddings(["How do I reset password?"])[0]
            results = vs_manager.search(query_emb, top_k=5)
            # Returns top 5 most similar chunks
        """
        
        try:
            # Prepare filter if provided
            filters = None
            if category_filter:
                filters = {
                    "key": "metadata.category",
                    "match": {"value": category_filter}
                }
            
            # Search in Qdrant
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding.tolist(),
                query_filter=filters,
                limit=top_k,
                score_threshold=threshold
            )
            
            # Format results
            results = []
            for scored_point in search_result:
                payload = scored_point.payload
                
                results.append({
                    "chunk_text": payload.get("chunk_text", ""),
                    "similarity_score": scored_point.score,
                    "doc_id": payload.get("doc_id"),
                    "section": payload.get("metadata", {}).get("section", "main"),
                    "source": payload.get("metadata", {}).get("source", "unknown"),
                    "metadata": payload.get("metadata", {}),
                    "timestamp": payload.get("timestamp")
                })
            
            logger.debug(f"Search returned {len(results)} results")
            return results
        
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document by ID."""
        
        try:
            point_id = _doc_id_to_point_id(doc_id)
            self.client.delete(
                collection_name=self.collection_name,
                points_selector={"ids": [point_id]}
            )
            logger.info(f"Deleted document: {doc_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            return False
    
    def clear_collection(self) -> bool:
        """Delete all documents in collection."""
        
        try:
            self.client.delete_collection(self.collection_name)
            
            # Recreate empty collection
            from qdrant_client.models import Distance, VectorParams
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=Distance.COSINE
                )
            )
            
            logger.info(f"Cleared collection: {self.collection_name}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Check vector store health and statistics."""
        
        try:
            collection_info = self.client.get_collection(self.collection_name)
            
            return {
                "status": "healthy",
                "collection": self.collection_name,
                "vector_count": collection_info.points_count,
                "vector_dim": self.embedding_dim,
                "connection": f"{self.qdrant_host}:{self.qdrant_port}"
            }
        
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "collection": self.collection_name
            }
    
    def get_stats(self) -> Dict:
        """Get vector store statistics."""
        
        try:
            collection_info = self.client.get_collection(self.collection_name)
            
            return {
                "collection_name": self.collection_name,
                "document_count": collection_info.points_count,
                "vector_dim": self.embedding_dim,
                "similarity_metric": "cosine",
                "indexed": collection_info.indexed_vectors_count
            }
        
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}


def _doc_id_to_point_id(doc_id: str) -> int:
    """
    Convert string doc_id to Qdrant point ID (unsigned int64).
    Uses hash to ensure consistent mapping.
    """
    import hashlib
    hash_bytes = hashlib.md5(doc_id.encode()).digest()
    # Convert first 8 bytes to unsigned int64
    point_id = int.from_bytes(hash_bytes[:8], byteorder='big', signed=False)
    return point_id
