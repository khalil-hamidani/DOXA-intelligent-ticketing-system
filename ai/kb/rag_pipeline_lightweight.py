#!/usr/bin/env python3
"""
Lightweight RAG pipeline using simple_retriever (JSON-based) + Mistral.
No heavy embeddings or ChromaDB initialization.
"""

import os
import json
from typing import List, Dict
from dotenv import load_dotenv
from mistralai import Mistral

# Load .env
_base_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_base_dir, ".env"))


class SimpleRetriever:
    """Retrieve chunks from index.json using keyword matching."""

    def __init__(self, index_path: str):
        with open(index_path, "r", encoding="utf-8") as f:
            self.chunks = json.load(f)

    def retrieve(self, query: str, k: int = 5, threshold: float = 0.0) -> List[Dict]:
        query_lower = query.lower()
        query_words = set(query_lower.split())

        scored = []
        for chunk in self.chunks:
            content_lower = chunk["content"].lower()
            content_words = set(content_lower.split())

            # Jaccard similarity
            intersection = query_words & content_words
            union = query_words | content_words
            similarity = len(intersection) / len(union) if union else 0.0

            # Boost by word frequency
            word_boost = sum(1 for w in query_words if w in content_lower) / max(len(query_words), 1) * 0.5
            final_score = min(1.0, similarity + word_boost)

            if final_score >= threshold:
                scored.append({
                    "content": chunk["content"],
                    "meta": chunk["meta"],
                    "score": round(final_score, 3),
                })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:k]


class RAGPipelineLightweight:
    """Lightweight RAG using SimpleRetriever + Mistral."""

    def __init__(self, index_path: str = None):
        if index_path is None:
            index_path = os.path.join(_base_dir, "index.json")
        self.retriever = SimpleRetriever(index_path)
        self.llm = Mistral(api_key=os.environ.get("MISTRAL_API_KEY"))

    def ask(self, query: str, k: int = 5, threshold: float = 0.0) -> str:
        # Retrieve
        chunks = self.retriever.retrieve(query, k=k, threshold=threshold)
        if not chunks:
            return "❌ No relevant documents found."

        # Build context
        context = "\n\n".join([c["content"] for c in chunks])

        # Generate response
        prompt = (
            f"You are a helpful assistant. Use the following context to answer the question.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {query}\n\n"
            f"Answer:"
        )

        model_name = os.environ.get("MISTRAL_MODEL", "mistral-large-latest")
        messages = [{"role": "user", "content": prompt}]

        resp = self.llm.chat.complete(model=model_name, messages=messages)

        # Extract response
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
        except Exception as e:
            return f"Error extracting response: {e}"


if __name__ == "__main__":
    rag = RAGPipelineLightweight()
    query = "What are the terms of service for Doxa?"
    print(f"Query: {query}\n")
    answer = rag.ask(query, k=5, threshold=0.1)
    print(answer)
