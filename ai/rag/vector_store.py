# rag/vector_store.py
"""Vector store for embeddings with in-memory and persistent options.

Supports:
- In-memory vector store (for testing, small datasets)
- Chroma vector store (persistent, production-ready)
- Similarity search with cosine similarity
- Filtering and metadata management
"""

from typing import List, Dict, Tuple, Optional
import numpy as np
from abc import ABC, abstractmethod
import json
from datetime import datetime

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False


class VectorStore(ABC):
    """Abstract vector store interface."""
    
    @abstractmethod
    def add_documents(self, documents: List[Dict], embeddings: np.ndarray) -> List[str]:
        """Add documents with embeddings.
        
        Args:
            documents: List of dicts with "id", "content", "metadata" keys
            embeddings: numpy array of shape (len(documents), embedding_dim)
            
        Returns:
            List of added document IDs
        """
        pass
    
    @abstractmethod
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        threshold: float = 0.0,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """Search for similar documents.
        
        Args:
            query_embedding: Query embedding (shape: (embedding_dim,))
            top_k: Number of results to return
            threshold: Minimum similarity score (0-1)
            filters: Optional metadata filters
            
        Returns:
            List of dicts with "id", "content", "similarity", "metadata"
        """
        pass
    
    @abstractmethod
    def get(self, doc_id: str) -> Optional[Dict]:
        """Retrieve a document by ID."""
        pass
    
    @abstractmethod
    def delete(self, doc_id: str) -> bool:
        """Delete a document."""
        pass
    
    @abstractmethod
    def size(self) -> int:
        """Get number of documents in store."""
        pass


class InMemoryVectorStore(VectorStore):
    """Simple in-memory vector store with cosine similarity."""
    
    def __init__(self):
        """Initialize in-memory store."""
        self.documents: Dict[str, Dict] = {}
        self.embeddings: Dict[str, np.ndarray] = {}
        self.id_to_idx: Dict[str, int] = {}
        self.idx_to_id: Dict[int, str] = {}
        self._next_idx = 0
    
    def add_documents(self, documents: List[Dict], embeddings: np.ndarray) -> List[str]:
        """Add documents with embeddings."""
        if len(documents) != len(embeddings):
            raise ValueError("Number of documents and embeddings must match")
        
        added_ids = []
        for doc, emb in zip(documents, embeddings):
            doc_id = doc.get("id", str(self._next_idx))
            self.documents[doc_id] = doc
            self.embeddings[doc_id] = emb
            self.id_to_idx[doc_id] = self._next_idx
            self.idx_to_id[self._next_idx] = doc_id
            self._next_idx += 1
            added_ids.append(doc_id)
        
        return added_ids
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        threshold: float = 0.0,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """Search using cosine similarity."""
        if not self.embeddings:
            return []
        
        # Build similarity matrix: cosine similarity
        embeddings_array = np.array([self.embeddings[doc_id] for doc_id in self.documents.keys()])
        
        # Normalize query embedding
        query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-10)
        embeddings_norm = embeddings_array / (np.linalg.norm(embeddings_array, axis=1, keepdims=True) + 1e-10)
        
        # Cosine similarity
        similarities = np.dot(embeddings_norm, query_norm)
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Build results
        results = []
        doc_ids = list(self.documents.keys())
        for idx in top_indices:
            doc_id = doc_ids[idx]
            similarity = float(similarities[idx])
            
            # Apply threshold
            if similarity < threshold:
                break
            
            # Apply filters
            if filters and not self._match_filters(self.documents[doc_id].get("metadata", {}), filters):
                continue
            
            results.append({
                "id": doc_id,
                "content": self.documents[doc_id].get("content", ""),
                "similarity": similarity,
                "metadata": self.documents[doc_id].get("metadata", {})
            })
        
        return results
    
    def get(self, doc_id: str) -> Optional[Dict]:
        """Get document by ID."""
        return self.documents.get(doc_id)
    
    def delete(self, doc_id: str) -> bool:
        """Delete document."""
        if doc_id in self.documents:
            idx = self.id_to_idx[doc_id]
            del self.documents[doc_id]
            del self.embeddings[doc_id]
            del self.id_to_idx[doc_id]
            del self.idx_to_id[idx]
            return True
        return False
    
    def size(self) -> int:
        """Get number of documents."""
        return len(self.documents)
    
    def _match_filters(self, metadata: Dict, filters: Dict) -> bool:
        """Check if metadata matches filters."""
        for key, value in filters.items():
            if metadata.get(key) != value:
                return False
        return True


class ChromaVectorStore(VectorStore):
    """Chroma-based vector store for production use."""
    
    def __init__(self, collection_name: str = "documents", persist_dir: Optional[str] = None):
        """Initialize Chroma vector store.
        
        Args:
            collection_name: Name of Chroma collection
            persist_dir: Directory for persistence (None for ephemeral)
        """
        if not CHROMA_AVAILABLE:
            raise ImportError("chromadb not installed. pip install chromadb")
        
        self.collection_name = collection_name
        self.persist_dir = persist_dir
        
        # Initialize Chroma client
        if persist_dir:
            settings = Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=persist_dir,
                anonymized_telemetry=False
            )
            self.client = chromadb.Client(settings)
        else:
            self.client = chromadb.Client()
        
        self.collection = self.client.get_or_create_collection(name=collection_name)
    
    def add_documents(self, documents: List[Dict], embeddings: np.ndarray) -> List[str]:
        """Add documents to Chroma collection."""
        if len(documents) != len(embeddings):
            raise ValueError("Number of documents and embeddings must match")
        
        ids = []
        texts = []
        metadatas = []
        embeddings_list = []
        
        for doc, emb in zip(documents, embeddings):
            doc_id = doc.get("id")
            if not doc_id:
                raise ValueError("Each document must have an 'id' field")
            
            ids.append(doc_id)
            texts.append(doc.get("content", ""))
            metadatas.append(doc.get("metadata", {}))
            embeddings_list.append(emb.tolist())
        
        # Add to Chroma
        self.collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings_list,
            metadatas=metadatas
        )
        
        return ids
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        threshold: float = 0.0,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """Search Chroma collection."""
        where = filters if filters else None
        
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k,
            where=where
        )
        
        # Format results
        formatted = []
        if results["ids"] and len(results["ids"]) > 0:
            for doc_id, content, distance, metadata in zip(
                results["ids"][0],
                results["documents"][0],
                results["distances"][0],
                results["metadatas"][0]
            ):
                # Chroma returns distances (larger = more different), convert to similarity
                similarity = 1 - (distance / 2)  # Normalize to 0-1
                
                if similarity >= threshold:
                    formatted.append({
                        "id": doc_id,
                        "content": content,
                        "similarity": similarity,
                        "metadata": metadata
                    })
        
        return formatted
    
    def get(self, doc_id: str) -> Optional[Dict]:
        """Get document by ID."""
        try:
            result = self.collection.get(ids=[doc_id])
            if result["ids"]:
                return {
                    "id": doc_id,
                    "content": result["documents"][0],
                    "metadata": result["metadatas"][0]
                }
        except Exception:
            pass
        return None
    
    def delete(self, doc_id: str) -> bool:
        """Delete document."""
        try:
            self.collection.delete(ids=[doc_id])
            return True
        except Exception:
            return False
    
    def size(self) -> int:
        """Get number of documents."""
        return self.collection.count()
    
    def persist(self):
        """Persist collection to disk (if initialized with persist_dir)."""
        if self.persist_dir:
            self.client.persist()


class VectorStoreFactory:
    """Factory for creating vector stores."""
    
    @staticmethod
    def create(
        store_type: str = "in_memory",
        **kwargs
    ) -> VectorStore:
        """Create a vector store.
        
        Args:
            store_type: "in_memory" | "chroma"
            **kwargs: Arguments passed to store constructor
                - chroma: collection_name, persist_dir
                
        Returns:
            VectorStore instance
        """
        if store_type == "in_memory":
            return InMemoryVectorStore()
        elif store_type == "chroma":
            return ChromaVectorStore(**kwargs)
        else:
            raise ValueError(f"Unknown vector store type: {store_type}")
