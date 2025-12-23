import os
from dotenv import load_dotenv

# Load .env from this folder if present (helps when running tests locally)
_base_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_base_dir, ".env"))

from retriever import ChromaRetriever
from mistralai import Mistral


class RAGPipelineMistral:
    """Pipeline RAG utilisant Mistral pour générer la réponse."""
    
    def __init__(self, persist_dir: str):
        self.retriever = ChromaRetriever(persist_dir)
        self.llm = Mistral(api_key=os.environ.get("MISTRAL_API_KEY"))

    def ask(self, query: str, k: int = 5, threshold: float = 0.0) -> str:
        # 1️⃣ Récupérer les chunks pertinents
        chunks = self.retriever.retrieve(query, k=k, threshold=threshold)
        if not chunks:
            return "Aucun document pertinent trouvé."
        
        # 2️⃣ Concaténer les chunks pour le contexte
        context = "\n\n".join([c["content"] for c in chunks])
        
        # 3️⃣ Générer la réponse avec Mistral
        prompt = f"Tu es un assistant. Utilise le contexte suivant pour répondre à la question.\n\nContexte:\n{context}\n\nQuestion: {query}\nRéponse:"

        model_name = os.environ.get("MISTRAL_MODEL", "mistral-large-latest")

        # Use the SDK chat API: provide a single user message
        messages = [{"role": "user", "content": prompt}]

        resp = self.llm.chat.complete(model=model_name, messages=messages)

        # Extract assistant content safely
        try:
            choice = resp.choices[0]
            msg = getattr(choice, "message", None)
            if msg is None:
                return str(resp)

            content = getattr(msg, "content", None)
            if isinstance(content, str):
                return content
            if isinstance(content, (list, tuple)):
                return "\n".join([c for c in content if isinstance(c, str)])
            return str(content)
        except Exception:
            return str(resp)
