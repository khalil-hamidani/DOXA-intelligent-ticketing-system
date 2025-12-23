import os
from rag_pipeline_mistral import RAGPipelineMistral

# Use absolute path based on script location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PERSIST_DIR = os.path.join(BASE_DIR, "chroma_db")

# Create the RAG pipeline with Mistral
rag = RAGPipelineMistral(persist_dir=PERSIST_DIR)

# Test query
query = "Quelles sont les details de plan entreprise ?"

# Get the answer
print("🔄 Retrieving documents and generating response...\n")
answer = rag.ask(query, k=5, threshold=0.5)

print("=== Question ===")
print(query)
print("\n=== Réponse RAG (Mistral) ===")
print(answer)
