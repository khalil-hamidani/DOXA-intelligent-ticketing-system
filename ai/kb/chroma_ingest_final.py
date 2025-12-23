import os
import json
import chromadb
from chromadb.utils import embedding_functions

# -----------------------------
# 1️⃣ Définir les chemins
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")
INDEX_JSON = os.path.join(BASE_DIR, "index.json")  # ton fichier de chunks

# Crée le dossier s’il n’existe pas
if not os.path.exists(CHROMA_DIR):
    os.makedirs(CHROMA_DIR)
    print(f"📂 Dossier de persistance créé : {CHROMA_DIR}")

# -----------------------------
# 2️⃣ Initialiser le client Chroma persistent
# -----------------------------
client = chromadb.PersistentClient(path=CHROMA_DIR)

# -----------------------------
# 3️⃣ Supprimer la collection existante si elle existe
# -----------------------------
if "kb_chunks" in [c.name for c in client.list_collections()]:
    client.delete_collection("kb_chunks")
    print("🗑 Collection existante supprimée.")

# -----------------------------
# 4️⃣ Créer la collection avec embedding
# -----------------------------
embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

collection = client.get_or_create_collection(
    name="kb_chunks",
    embedding_function=embedding_function
)
print("📚 Collection kb_chunks prête.")

# -----------------------------
# 5️⃣ Charger les chunks depuis index.json
# -----------------------------
with open(INDEX_JSON, "r", encoding="utf-8") as f:
    chunks = json.load(f)

print(f"Nombre de chunks à ingérer : {len(chunks)}")

# -----------------------------
# 6️⃣ Ajouter les chunks en batch
# -----------------------------
documents = [chunk["content"] for chunk in chunks]
metadatas = [chunk["meta"] for chunk in chunks]
ids = [f"{chunk['meta']['source']}_{chunk['meta']['chunk_id']}" for chunk in chunks]

collection.add(
    documents=documents,
    metadatas=metadatas,
    ids=ids
)

print(f"✅ {len(chunks)} chunks ingérés dans la collection.")

# -----------------------------
# 7️⃣ Vérification rapide du retrieval
# -----------------------------
query = "service"  # exemple de test
results = collection.query(
    query_texts=[query],
    n_results=5
)

print("Résultats retrieval test:")
for doc, meta, dist in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
    similarity = 1 - dist
    print(f"- Document: {doc[:100]}... | Meta: {meta} | Similarity: {similarity:.3f}")
