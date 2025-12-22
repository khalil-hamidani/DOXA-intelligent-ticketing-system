"""Check API signatures"""
import sys
from pathlib import Path
import inspect

sys.path.insert(0, str(Path(__file__).parent))

print("Checking API signatures...")

# Check evaluate
from agents import evaluator
sig = inspect.signature(evaluator.evaluate)
print(f"evaluate signature: {sig}")

# Check handle_feedback
from agents import feedback_handler
sig = inspect.signature(feedback_handler.handle_feedback)
print(f"handle_feedback signature: {sig}")

# Check escalate_ticket
from agents import escalation_manager
sig = inspect.signature(escalation_manager.escalate_ticket)
print(f"escalate_ticket signature: {sig}")

# Check plan_ticket_resolution
from agents import query_planner
sig = inspect.signature(query_planner.plan_ticket_resolution)
print(f"plan_ticket_resolution signature: {sig}")

# Check analyze_and_reformulate_with_validation
from agents import query_analyzer
sig = inspect.signature(query_analyzer.analyze_and_reformulate_with_validation)
print(f"analyze_and_reformulate_with_validation signature: {sig}")

print("\nDone!")
