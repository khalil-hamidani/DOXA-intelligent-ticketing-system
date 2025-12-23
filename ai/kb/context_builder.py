# context.py

class ContextBuilder:
    def __init__(self, max_chars: int = 3000):
        """
        max_chars : limite de taille du contexte (sécurité pour le LLM)
        """
        self.max_chars = max_chars

    def build(self, retrieved_docs: list) -> str:
        """
        retrieved_docs : sortie du ChromaRetriever.retrieve()
        """
        if not retrieved_docs:
            print("⚠️ Aucun document récupéré")
            return ""

        context_parts = []
        total_length = 0

        for i, doc in enumerate(retrieved_docs, start=1):
            # sécurité si content absent
            content = doc.get("content")
            if not content:
                print(f"⚠️ Document {i} vide, ignoré")
                continue

            content = content.strip()
            if not content:
                print(f"⚠️ Document {i} ne contient que des espaces, ignoré")
                continue

            meta = doc.get("meta") or {}
            source = meta.get("source", "unknown")
            score = doc.get("score", 0)

            block = (
                f"[Document {i}]\n"
                f"Source: {source}\n"
                f"Score: {score}\n"
                f"Content:\n{content}\n"
            )

            # limite de taille
            if total_length + len(block) > self.max_chars:
                print(f"⚠️ Limite max_chars atteinte après {i-1} documents")
                break

            context_parts.append(block)
            total_length += len(block)

        if not context_parts:
            print("⚠️ Aucun document n’a été ajouté au contexte")
            return ""

        return "\n---\n".join(context_parts)
