import os
import json
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

# =====================================================
# Paths
# =====================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.join(BASE_DIR, "index.json")
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")

# =====================================================
# Load chunks
# =====================================================
with open(INDEX_PATH, "r", encoding="utf-8") as f:
    chunks = json.load(f)

print(f"✅ {len(chunks)} chunks loaded")

# =====================================================
# Embedding function
# =====================================================
embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# =====================================================
# ChromaDB client (AUTO-PERSIST)
# =====================================================
client = chromadb.Client(
    Settings(
        persist_directory=CHROMA_DIR,
        anonymized_telemetry=False
    )
)

collection = client.get_or_create_collection(
    name="kb_chunks",
    embedding_function=embedding_function
)

# =====================================================
# Add chunks
# =====================================================
collection.add(
    documents=[c["content"] for c in chunks],
    metadatas=[c["meta"] for c in chunks],
    ids=[
        f"{c['meta']['source']}_{c['meta']['chunk_id']}"
        for c in chunks
    ]
)

print("🎉 Embedding + storage DONE (auto-persisted)")
