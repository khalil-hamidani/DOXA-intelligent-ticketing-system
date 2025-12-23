# test_context.py
import os

from retriever import ChromaRetriever
from context_builder import ContextBuilder

# Use absolute path based on script location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")

retriever = ChromaRetriever(persist_dir=CHROMA_DIR)

# récupère les 5 documents les plus proches sans threshold
results = retriever.retrieve("conditions de service", k=5, threshold=0.0)

print(f"📄 Nombre de documents récupérés : {len(results)}")
for i, r in enumerate(results, start=1):
    print(f"Document {i} preview:", r["content"][:100], "...")

# construit le contexte
builder = ContextBuilder(max_chars=3000)
context = builder.build(results)

print("\n===== CONTEXT BUILT =====\n")
print(context)
