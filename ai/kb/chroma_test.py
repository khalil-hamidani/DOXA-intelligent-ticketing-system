import os
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

# =====================================================
# Paths (IDENTIQUES à chroma_ingest.py)
# =====================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")

# =====================================================
# Embedding function (OBLIGATOIRE)
# =====================================================
embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# =====================================================
# Chroma client (LOAD EXISTING DB)
# =====================================================
client = chromadb.Client(
    Settings(
        persist_directory=CHROMA_DIR,
        anonymized_telemetry=False
    )
)

# ⚠️ IMPORTANT : get_or_create_collection
collection = client.get_or_create_collection(
    name="kb_chunks",
    embedding_function=embedding_function
)

# =====================================================
# Test query
# =====================================================
query = "données personnelles"

results = collection.query(
    query_texts=[query],
    n_results=3
)

# =====================================================
# Display results
# =====================================================
print("\n🔎 QUESTION:", query)

for i, doc in enumerate(results["documents"][0]):
    meta = results["metadatas"][0][i]
    print(f"\n--- Résultat {i+1} ---")
    print("Source:", meta["source"])
    print(doc[:500], "...")
