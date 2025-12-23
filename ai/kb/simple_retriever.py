#!/usr/bin/env python3
"""JSON-based retriever that doesn't depend on ChromaDB."""

import json
import os
from typing import List, Dict


class SimpleRetriever:
    """Retrieve chunks from index.json using keyword matching and fuzzy search."""

    def __init__(self, index_path: str):
        self.index_path = index_path
        with open(index_path, "r", encoding="utf-8") as f:
            self.chunks = json.load(f)
        print(f"✅ Loaded {len(self.chunks)} chunks from {index_path}")

    def retrieve(self, query: str, k: int = 5, threshold: float = 0.0) -> List[Dict]:
        """
        Retrieve top-k chunks matching the query using keyword overlap.
        
        Args:
            query: Search query string
            k: Number of results to return
            threshold: Minimum relevance score (0.0-1.0)
        
        Returns:
            List of documents with content, meta, and score
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())

        scored_chunks = []
        for chunk in self.chunks:
            content_lower = chunk["content"].lower()
            content_words = set(content_lower.split())

            # Calculate simple Jaccard similarity
            intersection = query_words & content_words
            union = query_words | content_words
            similarity = len(intersection) / len(union) if union else 0.0

            # Also boost if any query word appears in content
            word_boost = sum(1 for word in query_words if word in content_lower) / max(len(query_words), 1) * 0.5

            final_score = min(1.0, similarity + word_boost)

            if final_score >= threshold:
                scored_chunks.append({
                    "content": chunk["content"],
                    "meta": chunk["meta"],
                    "score": round(final_score, 3),
                })

        # Sort by score descending
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        return scored_chunks[:k]


if __name__ == "__main__":
    retriever = SimpleRetriever("index.json")
    results = retriever.retrieve("conditions de service", k=5, threshold=0.0)
    print(f"\n📄 Found {len(results)} results:")
    for i, r in enumerate(results, 1):
        print(f"\n{i}. Score: {r['score']} | Source: {r['meta']['source']}")
        print(f"   {r['content'][:150]}...")
