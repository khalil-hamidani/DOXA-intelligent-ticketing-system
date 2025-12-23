import os
from retriever import ChromaRetriever

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")

retriever = ChromaRetriever(CHROMA_DIR)

query = "données personnelles"
docs = retriever.retrieve(query, k=3, threshold=0.25)

print(f"Retrieved {len(docs)} documents\n")

for d in docs:
    print("Score:", d["score"])
    print("Source:", d["meta"]["source"])
    print(d["content"][:300])
    print("-" * 40)
