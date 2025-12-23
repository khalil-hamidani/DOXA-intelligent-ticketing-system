#!/usr/bin/env python3
"""Ingest chunks from index.json into ChromaDB with batching."""

import os
import json
import chromadb
from chromadb.utils import embedding_functions

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")
INDEX_JSON = os.path.join(BASE_DIR, "index.json")

# Ensure directory exists
os.makedirs(CHROMA_DIR, exist_ok=True)

# Initialize ChromaDB
client = chromadb.PersistentClient(path=CHROMA_DIR)

# Delete existing collection
if "kb_chunks" in [c.name for c in client.list_collections()]:
    client.delete_collection("kb_chunks")
    print("🗑 Deleted existing collection.")

# Create new collection
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)
collection = client.get_or_create_collection(
    name="kb_chunks",
    embedding_function=embedding_fn
)
print("✅ Created kb_chunks collection.")

# Load chunks from index.json
with open(INDEX_JSON, "r", encoding="utf-8") as f:
    chunks = json.load(f)

print(f"📊 Loaded {len(chunks)} chunks from index.json")

# Ingest in batches to avoid timeout
BATCH_SIZE = 50
for i in range(0, len(chunks), BATCH_SIZE):
    batch = chunks[i:i + BATCH_SIZE]
    
    documents = [c["content"] for c in batch]
    metadatas = [c["meta"] for c in batch]
    ids = [f"{c['meta']['source']}_{c['meta']['chunk_id']}" for c in batch]
    
    collection.add(documents=documents, metadatas=metadatas, ids=ids)
    print(f"  ✓ Ingested batch {i//BATCH_SIZE + 1} ({len(batch)} chunks)")

print(f"✅ Successfully ingested {len(chunks)} chunks into ChromaDB")

# Quick test
results = collection.query(query_texts=["service"], n_results=3)
print("\n🔍 Quick retrieval test (query='service'):")
for doc, meta, dist in zip(
    results["documents"][0],
    results["metadatas"][0],
    results["distances"][0]
):
    similarity = 1 - dist
    print(f"  - Similarity: {similarity:.3f} | Source: {meta.get('source')} | Preview: {doc[:80]}...")
