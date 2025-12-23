import chromadb
from chromadb.utils import embedding_functions

class ChromaRetriever:
    def __init__(self, persist_dir: str):
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        self.client = chromadb.PersistentClient(path=persist_dir)

        # Try to get existing collection first, then create if needed
        try:
            self.collection = self.client.get_collection(
                name="kb_chunks",
                embedding_function=self.embedding_function
            )
        except Exception:
            # Fall back to creating new collection if it doesn't exist
            self.collection = self.client.get_or_create_collection(
                name="kb_chunks",
                embedding_function=self.embedding_function
            )

    def retrieve(self, query: str, k=5, threshold=0.0):
        results = self.collection.query(
            query_texts=[query],
            n_results=k
        )

        documents = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        ):
            similarity = 1 - dist
            if similarity >= threshold:
                documents.append({
                    "content": doc,
                    "meta": meta,
                    "score": round(similarity, 3)
                })

        documents.sort(key=lambda x: x["score"], reverse=True)
        return documents
