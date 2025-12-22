"""Quick diagnostic test"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from models import Ticket
from agents.query_analyzer import analyze_and_reformulate_with_validation
from agents.unified_classifier import classify_unified
from agents.evaluator import evaluate

# Test 1: Reformulation
print("Test 1: Reformulation")
ticket = Ticket(
    id="T001",
    subject="Can't login",
    description="Password stopped working",
    client_name="User",
    email="user@example.com"
)

try:
    result = analyze_and_reformulate_with_validation(ticket)
    print(f"  ✓ Keys: {list(result.keys())}")
    print(f"  ✓ Reformulation: {result['reformulation'][:50]}...")
except Exception as e:
    print(f"  ✗ Error: {type(e).__name__}: {e}")

# Test 2: Classifier with setting classification
print("\nTest 2: Classifier with classification attribute")
ticket2 = Ticket(
    id="T002",
    subject="System down",
    description="Platform not responding",
    client_name="Admin",
    email="admin@example.com"
)

try:
    classification = classify_unified(ticket2)
    print(f"  ✓ Classification: {classification.primary_category}")
    print(f"  ✓ Has severity: {hasattr(classification, 'severity')}")
    
    # Try to set it
    classification.severity = "critical"
    print(f"  ✓ Set severity: {classification.severity}")
    
    # Try to assign to ticket
    ticket2.classification = classification
    print(f"  ✗ Should not be able to assign to ticket (no field)")
except AttributeError as e:
    print(f"  ✗ AttributeError: {e}")
except Exception as e:
    print(f"  ✗ Error: {type(e).__name__}: {e}")

# Test 3: Evaluator signature
print("\nTest 3: Evaluator signature")
ticket3 = Ticket(
    id="T003",
    subject="Test",
    description="Test",
    client_name="User",
    email="user@example.com"
)

try:
    # Check what evaluate expects
    import inspect
    sig = inspect.signature(evaluate)
    print(f"  ✓ Signature: {sig}")
    
    # Call it
    result = evaluate(ticket3)
    print(f"  ✓ Result keys: {list(result.keys())}")
except Exception as e:
    print(f"  ✗ Error: {type(e).__name__}: {e}")

# Test 4: Feedback handler
print("\nTest 4: Feedback handler")
from agents.feedback_handler import handle_feedback

ticket4 = Ticket(
    id="T004",
    subject="Test",
    description="Test",
    client_name="User",
    email="user@example.com"
)

try:
    feedback = {"sentiment": "positive", "helpful": True, "comment": "Great!"}
    result = handle_feedback(ticket4, feedback)
    print(f"  ✓ Action: {result.get('action')}")
    print(f"  ✓ Result keys: {list(result.keys())}")
except Exception as e:
    print(f"  ✗ Error: {type(e).__name__}: {e}")
