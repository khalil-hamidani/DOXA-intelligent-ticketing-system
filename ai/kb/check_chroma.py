#!/usr/bin/env python3
"""Quick check of ChromaDB collection status without embeddings."""

import os
import json
import chromadb

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")
INDEX_JSON = os.path.join(BASE_DIR, "index.json")

client = chromadb.PersistentClient(path=CHROMA_DIR)

# List existing collections
collections = client.list_collections()
print(f"📚 Collections in {CHROMA_DIR}:")
for col in collections:
    print(f"  - {col.name}")
    # Try to get count
    try:
        count = col.count()
        print(f"    Count: {count}")
    except Exception as e:
        print(f"    Error getting count: {e}")

# Load index.json info
with open(INDEX_JSON, "r", encoding="utf-8") as f:
    chunks = json.load(f)
print(f"\n📊 index.json contains {len(chunks)} chunks ready to ingest")

# Try getting the kb_chunks collection without embedding
try:
    print("\n🔍 Checking kb_chunks collection without embedding function...")
    col = client.get_collection(name="kb_chunks")
    count = col.count()
    print(f"✅ kb_chunks collection has {count} documents")
except Exception as e:
    print(f"❌ Error: {e}")
