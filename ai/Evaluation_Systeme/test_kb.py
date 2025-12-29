#!/usr/bin/env python3
"""Test KB retrieval from Evaluation_Systeme directory"""

import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AI_DIR = os.path.dirname(SCRIPT_DIR)
KB_DIR = os.path.join(AI_DIR, "kb")

sys.path.insert(0, AI_DIR)
sys.path.insert(0, KB_DIR)

from unified_kb import UnifiedKnowledgeBase

kb = UnifiedKnowledgeBase(use_json=True)

# Test with actual questions
test_queries = [
    "Doxa",
    "prix plan Pro",
    "loi 25-11 Algerie",
    "ajouter membre",
    "erreur Email non reconnu",
]

print("\n" + "=" * 60)
print("KB RETRIEVAL TEST")
print("=" * 60)

for q in test_queries:
    results = kb.retrieve(q, k=3, threshold=0.0)
    print(f"\nQuery: {q}")
    print(f"  Results count: {len(results)}")
    if results:
        print(f"  Best score: {results[0]['score']}")
        preview = results[0]["content"][:100].replace("\n", " ")
        print(f"  Content: {preview}...")
    else:
        print("  NO RESULTS!")

print("\n" + "=" * 60)
