import os
import sys
import pytest
import chromadb
from chromadb.utils import embedding_functions

# Get paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB_DIR = os.path.join(BASE_DIR, "kb")
CHROMA_DIR = os.path.join(KB_DIR, "chroma_db")

def test_kb_avg_similarity_threshold():
    """Test that KB retrieval returns average similarity >= 0.80"""
    THRESHOLD = float(os.getenv("KB_SIMILARITY_THRESHOLD", "0.80"))
    
    # Skip if chroma_db doesn't exist
    if not os.path.exists(CHROMA_DIR):
        pytest.skip("ChromaDB not initialized at " + CHROMA_DIR)
    
    # Initialize client
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    
    # Try to get collection
    try:
        collection = client.get_collection(name="kb_chunks")
    except Exception:
        pytest.skip("Collection kb_chunks not found")
    
    # Test queries
    queries = ["service", "connexion", "facturation", "mot de passe", "paiement"]
    similarities = []
    
    for q in queries:
        results = collection.query(query_texts=[q], n_results=1)
        distances = results.get("distances", [[]])[0]
        if distances:
            # Convert distance to similarity (1 - distance)
            sim = 1.0 - distances[0]
            similarities.append(sim)
    
    assert similarities, "No retrieval results found"
    avg_sim = sum(similarities) / len(similarities)
    
    print(f"\nAverage similarity: {avg_sim:.3f} (threshold: {THRESHOLD})")
    assert avg_sim >= THRESHOLD, f"avg_similarity {avg_sim:.3f} < threshold {THRESHOLD}"
