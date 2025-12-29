#!/usr/bin/env python3
"""Debug the full evaluation pipeline"""

import os
import sys
import logging

logging.basicConfig(level=logging.INFO)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AI_DIR = os.path.dirname(SCRIPT_DIR)
KB_DIR = os.path.join(AI_DIR, "kb")

sys.path.insert(0, AI_DIR)
sys.path.insert(0, KB_DIR)

print("=" * 60)
print("EVALUATION PIPELINE DEBUG")
print("=" * 60)

# Import the evaluation script's EvaluationPipeline
from evaluation_script import EvaluationPipeline, MODULES_AVAILABLE

print(f"\nModule availability: {MODULES_AVAILABLE}")

# Create pipeline
pipeline = EvaluationPipeline(team_name="DEBUG")
print(f"\nKB object: {pipeline.kb}")
print(f"KB initialized: {pipeline.kb.initialized if pipeline.kb else 'N/A'}")

# Test KB directly
if pipeline.kb and pipeline.kb.initialized:
    results = pipeline.kb.retrieve("Doxa", k=3, threshold=0.1)
    print(f"Direct KB retrieval: {len(results)} results")
else:
    print("KB not available!")

# Test _process_question_through_kb
print("\nTesting _process_question_through_kb...")
answer = pipeline._process_question_through_kb("Qu'est-ce que Doxa ?")
print(f"Answer from KB: {answer[:200] if answer else 'None'}...")

# Test process_question
print("\nTesting process_question...")
result = pipeline.process_question("TEST001", "Qu'est-ce que Doxa ?")
print(f"Result: {result}")
