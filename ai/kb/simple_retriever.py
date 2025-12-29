#!/usr/bin/env python3
"""JSON-based retriever that doesn't depend on ChromaDB."""

import json
import os
import logging
import re
from typing import List, Dict, Set

logger = logging.getLogger(__name__)

# Synonym mappings for better matching
SYNONYMS = {
    "prix": [
        "tarif",
        "cout",
        "coute",
        "dzd",
        "mois",
        "facturation",
        "plan",
        "starter",
        "pro",
        "enterprise",
    ],
    "tarif": ["prix", "cout", "coute", "dzd", "mois", "facturation"],
    "projet": ["projets", "kanban", "agile", "waterfall", "creer"],
    "membre": ["membres", "equipe", "utilisateur", "utilisateurs", "inviter"],
    "securite": ["chiffrement", "ssl", "tls", "aes", "protection", "donnees"],
    "erreur": ["probleme", "bug", "bloque", "impossible", "echoue"],
    "integrer": ["integration", "integrations", "slack", "teams", "api", "zapier"],
    "exporter": ["export", "csv", "pdf", "json", "telecharger"],
    "supprimer": ["suppression", "archiver", "effacer", "retirer"],
    "notifier": ["notification", "notifications", "alerte", "email"],
    "essai": ["gratuit", "trial", "tester", "14"],
    "conformite": ["loi", "25-11", "anpdp", "rgpd", "protection"],
}


def normalize_text(text: str) -> str:
    """Normalize text by removing accents and converting to lowercase."""
    # Simple accent removal
    replacements = {
        "é": "e",
        "è": "e",
        "ê": "e",
        "ë": "e",
        "à": "a",
        "â": "a",
        "ä": "a",
        "î": "i",
        "ï": "i",
        "ô": "o",
        "ö": "o",
        "ù": "u",
        "û": "u",
        "ü": "u",
        "ç": "c",
    }
    text = text.lower()
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def expand_query(query: str) -> Set[str]:
    """Expand query with synonyms for better matching."""
    words = set(re.findall(r"\w+", normalize_text(query)))
    expanded = set(words)

    for word in words:
        if word in SYNONYMS:
            expanded.update(SYNONYMS[word])
        # Also check if any synonym key contains this word
        for key, syns in SYNONYMS.items():
            if word in syns or word == key:
                expanded.add(key)
                expanded.update(syns)

    return expanded


class SimpleRetriever:
    """Retrieve chunks from index.json using keyword matching and fuzzy search."""

    def __init__(self, index_path: str):
        self.index_path = index_path
        with open(index_path, "r", encoding="utf-8") as f:
            self.chunks = json.load(f)
        logger.info(f"Loaded {len(self.chunks)} chunks from {index_path}")

    def retrieve(self, query: str, k: int = 5, threshold: float = 0.0) -> List[Dict]:
        """
        Retrieve top-k chunks matching the query using keyword overlap with synonym expansion.

        Args:
            query: Search query string
            k: Number of results to return
            threshold: Minimum relevance score (0.0-1.0)

        Returns:
            List of documents with content, meta, and score
        """
        # Expand query with synonyms
        query_words = expand_query(query)
        query_normalized = normalize_text(query)

        scored_chunks = []
        for chunk in self.chunks:
            content = chunk["content"]
            content_normalized = normalize_text(content)
            content_words = set(re.findall(r"\w+", content_normalized))

            # Calculate Jaccard similarity with expanded query
            intersection = query_words & content_words
            union = query_words | content_words
            similarity = len(intersection) / len(union) if union else 0.0

            # Boost if query words appear in content
            word_boost = 0.0
            for word in query_words:
                if word in content_normalized:
                    word_boost += 0.1
            word_boost = min(0.5, word_boost)  # Cap boost at 0.5

            # Extra boost for exact phrase matches
            phrase_boost = 0.0
            # Check for important terms directly
            if "pro" in query_normalized and (
                "pro" in content_normalized or "11 850" in content or "11850" in content
            ):
                phrase_boost += 0.3
            if "prix" in query_normalized or "tarif" in query_normalized:
                if "dzd" in content_normalized or "mois" in content_normalized:
                    phrase_boost += 0.2
            if "starter" in query_normalized and "starter" in content_normalized:
                phrase_boost += 0.3
            if "enterprise" in query_normalized and "enterprise" in content_normalized:
                phrase_boost += 0.3

            final_score = min(1.0, similarity + word_boost + phrase_boost)

            if final_score >= threshold:
                scored_chunks.append(
                    {
                        "content": content,
                        "meta": chunk.get("meta", {}),
                        "score": round(final_score, 3),
                    }
                )

        # Sort by score descending
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        return scored_chunks[:k]


if __name__ == "__main__":
    retriever = SimpleRetriever("index.json")
    results = retriever.retrieve("Quel est le prix du plan Pro ?", k=5, threshold=0.0)
    print(f"\nFound {len(results)} results:")
    for i, r in enumerate(results, 1):
        print(
            f"\n{i}. Score: {r['score']} | Source: {r['meta'].get('source', 'unknown')}"
        )
        print(f"   {r['content'][:150]}...")
