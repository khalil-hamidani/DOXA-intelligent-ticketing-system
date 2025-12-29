#!/usr/bin/env python3
"""Debug KB initialization in evaluation context"""

import os
import sys
import logging

logging.basicConfig(level=logging.DEBUG)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AI_DIR = os.path.dirname(SCRIPT_DIR)
KB_DIR = os.path.join(AI_DIR, "kb")

print(f"SCRIPT_DIR: {SCRIPT_DIR}")
print(f"AI_DIR: {AI_DIR}")
print(f"KB_DIR: {KB_DIR}")

sys.path.insert(0, AI_DIR)
sys.path.insert(0, KB_DIR)

print("\nImporting UnifiedKnowledgeBase...")
from unified_kb import UnifiedKnowledgeBase

print("Creating KB instance...")
kb = UnifiedKnowledgeBase(use_json=True)
print(f"KB initialized: {kb.initialized}")
print(f"KB retriever type: {type(kb.retriever)}")

if kb.initialized:
    print("\nTesting retrieval...")
    results = kb.retrieve("Doxa", k=3, threshold=0.1)
    print(f"Results count: {len(results)}")
    if results:
        print(f"First result score: {results[0]['score']}")
        content = results[0]["content"][:100].replace("\n", " ")
        print(f"First result content: {content}")
else:
    print("KB NOT initialized - checking why...")
    index_path = os.path.join(KB_DIR, "index.json")
    print(f"index.json exists: {os.path.exists(index_path)}")
