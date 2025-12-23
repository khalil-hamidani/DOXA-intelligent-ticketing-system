"""
Final Verification Tests - DOXA System
Tests all agents and workflows with proper Ticket structure.
"""

import sys
from pathlib import Path
from typing import Dict
import traceback

# Add ai folder to path
sys.path.insert(0, str(Path(__file__).parent))

from models import Ticket
from agents.validator import validate_ticket
from agents.scorer import score_ticket
from agents.query_analyzer import analyze_and_reformulate_with_validation
from agents.unified_classifier import classify_unified
from agents.query_planner import plan_ticket_resolution
from agents.evaluator import evaluate
from agents.response_composer import compose_response
from agents.feedback_handler import handle_feedback
from agents.escalation_manager import escalate_ticket


class TestRunner:
    """Simple test runner with no external dependencies."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def test(self, name: str, func):
        """Run a single test."""
        try:
            func()
            self.passed += 1
            print(f"  ✓ {name}")
            return True
        except AssertionError as e:
            self.failed += 1
            self.errors.append((name, str(e)))
            print(f"  ✗ {name}: {e}")
            return False
        except Exception as e:
            self.failed += 1
            error_msg = f"{type(e).__name__}: {str(e)[:100]}"
            self.errors.append((name, error_msg))
            print(f"  ✗ {name}: {error_msg}")
            return False
    
    def summary(self):
        """Print test summary."""
        total = self.passed + self.failed
        print(f"\n{'='*70}")
        print(f"TEST SUMMARY: {self.passed}/{total} passed, {self.failed} failed")
        print(f"{'='*70}")
        
        if self.errors:
            print("\nFailed tests:")
            for test_name, error in self.errors:
                print(f"  • {test_name}")
                print(f"    └─ {error[:80]}")
        
        return self.failed == 0


# Helper function to create test tickets
def create_ticket(ticket_id: str, subject: str, description: str, **kwargs) -> Ticket:
    """Create a test ticket with required fields."""
    defaults = {
        "client_name": "Test User",
        "email": "test@example.com",
        "category": "technique",
    }
    defaults.update(kwargs)
    return Ticket(
        id=ticket_id,
        subject=subject,
        description=description,
        **defaults
    )


print("\n" + "="*70)
print("DOXA FINAL VERIFICATION TEST SUITE")
print("="*70)

runner = TestRunner()

# ============================================================================
# UNIT TESTS
# ============================================================================

print("\n[VALIDATOR AGENT]")

def test_valid_ticket():
    ticket = create_ticket(
        "T001",
        "Cannot login to account",
        "I've been trying to login for 2 hours but getting error 401"
    )
    result = validate_ticket(ticket)
    assert result["valid"] == True, f"Valid ticket should pass: {result}"
    assert result["confidence"] >= 0.5

def test_invalid_empty_subject():
    ticket = create_ticket("T002", "", "Help me please with a long description")
    result = validate_ticket(ticket)
    assert result["valid"] == False, "Empty subject should be invalid"

runner.test("Accept valid ticket", test_valid_ticket)
runner.test("Reject empty subject", test_invalid_empty_subject)

# SCORER TESTS
print("\n[SCORER AGENT]")

def test_critical_score():
    ticket = create_ticket(
        "T003",
        "System down - critical",
        "Production system is completely down. No users can access.",
    )
    result = score_ticket(ticket)
    assert result["score"] >= 70, f"Critical should score high: {result['score']}"
    assert 0 <= result["score"] <= 100

def test_low_priority_score():
    ticket = create_ticket(
        "T004",
        "UI suggestion",
        "Button could be a different color",
        category="feature_request"
    )
    result = score_ticket(ticket)
    assert result["score"] <= 50, f"Low priority should score low: {result['score']}"

runner.test("Score critical issue ≥70", test_critical_score)
runner.test("Score low priority ≤50", test_low_priority_score)

# ANALYZER TESTS
print("\n[QUERY ANALYZER]")

def test_keyword_extraction():
    ticket = create_ticket(
        "T005",
        "Password reset error",
        "Error code 401 on Windows 10, need password reset"
    )
    analysis = analyze_and_reformulate_with_validation(ticket)
    assert "keywords" in analysis, "Keywords not extracted"
    assert len(analysis["keywords"]) > 0, "No keywords found"

def test_reformulation_quality():
    ticket = create_ticket(
        "T006",
        "Can't login",
        "Password stopped working after update"
    )
    analysis = analyze_and_reformulate_with_validation(ticket)
    assert "reformulation" in analysis, "Reformulation missing"
    assert len(analysis["reformulation"]) > 10, "Reformulation too short"

runner.test("Extract keywords", test_keyword_extraction)
runner.test("Generate reformulation", test_reformulation_quality)

# CLASSIFIER TESTS
print("\n[UNIFIED CLASSIFIER]")

def test_auth_classification():
    ticket = create_ticket(
        "T007",
        "Cannot reset password",
        "I forgot password and cannot login",
        category="authentication"
    )
    result = classify_unified(ticket)
    assert result.primary_category == "authentification", f"Wrong category: {result.primary_category}"
    overall = result.overall_confidence()
    assert 0 <= overall <= 1.0, f"Invalid confidence: {overall}"

def test_billing_classification():
    ticket = create_ticket(
        "T008",
        "Wrong charge on invoice",
        "Charged $100 twice this month",
        category="billing"
    )
    result = classify_unified(ticket)
    assert result.primary_category == "facturation", f"Wrong category: {result.primary_category}"
    assert result.confidence_category >= 0.5

runner.test("Classify authentication", test_auth_classification)
runner.test("Classify billing", test_billing_classification)

# PLANNER TESTS
print("\n[QUERY PLANNER]")

def test_plan_kb_retrieval():
    ticket = create_ticket(
        "T009",
        "How to change password",
        "I want to change my password for security",
        category="authentication"
    )
    analysis = analyze_and_reformulate_with_validation(ticket)
    classification = classify_unified(ticket)
    ticket.keywords = analysis.get("keywords", [])
    
    plan = plan_ticket_resolution(ticket)
    assert plan.resolution_path in ["kb_retrieval", "escalation"], f"Invalid path: {plan.resolution_path}"

def test_plan_critical_escalation():
    ticket = create_ticket(
        "T010",
        "CRITICAL: System completely down",
        "Entire platform not responding, all users affected"
    )
    classification = classify_unified(ticket)
    classification.severity = "critical"
    ticket.classification = classification
    
    plan = plan_ticket_resolution(ticket)
    assert plan.resolution_path == "escalation", f"Critical should escalate: {plan.resolution_path}"

runner.test("Plan KB retrieval", test_plan_kb_retrieval)
runner.test("Escalate critical issues", test_plan_critical_escalation)

# EVALUATOR TESTS
print("\n[EVALUATOR AGENT]")

def test_high_confidence_evaluation():
    ticket = create_ticket("T011", "Password reset", "Help resetting")
    result = evaluate(
        ticket,
        "Click Forgot Password on login page",
        kb_confident=True,
        kb_limit_reached=False
    )
    assert result["confidence"] >= 0.6, f"High confidence too low: {result['confidence']}"

def test_low_confidence_evaluation():
    ticket = create_ticket("T012", "Unknown error", "Something is wrong")
    result = evaluate(
        ticket,
        "Try restarting",
        kb_confident=False,
        kb_limit_reached=True
    )
    assert "confidence" in result, "Confidence missing"
    assert isinstance(result["confidence"], (int, float))

runner.test("Evaluate high confidence", test_high_confidence_evaluation)
runner.test("Evaluate low confidence", test_low_confidence_evaluation)

# COMPOSER TESTS
print("\n[RESPONSE COMPOSER]")

def test_compose_email():
    ticket = create_ticket("T013", "Password reset", "Help", client_name="Alice")
    email_body = compose_response(
        ticket,
        "Click Forgot Password",
        evaluation={"confidence": 0.85, "escalate": False}
    )
    assert isinstance(email_body, str), f"Should return string: {type(email_body)}"
    assert len(email_body) > 0, "Email body empty"

runner.test("Compose email response", test_compose_email)

# FEEDBACK TESTS
print("\n[FEEDBACK HANDLER]")

def test_positive_feedback():
    ticket = create_ticket("T014", "Test", "Test description")
    feedback = {
        "sentiment": "positive",
        "helpful": True,
        "comment": "Great!"
    }
    result = handle_feedback(ticket, feedback)
    assert result["action"] == "close", f"Positive should close: {result['action']}"

def test_negative_feedback():
    ticket = create_ticket("T015", "Test", "Test description")
    feedback = {
        "sentiment": "negative",
        "helpful": False,
        "comment": "Didn't work"
    }
    result = handle_feedback(ticket, feedback)
    assert result["action"] in ["retry", "escalate"], f"Invalid action: {result['action']}"

runner.test("Positive feedback closes", test_positive_feedback)
runner.test("Negative feedback retries/escalates", test_negative_feedback)

# ESCALATION TESTS
print("\n[ESCALATION MANAGER]")

def test_escalate_ticket():
    ticket = create_ticket("T016", "Critical issue", "System down")
    result = escalate_ticket(ticket, "Test escalation", {})
    assert "escalation_id" in result, "Escalation ID missing"
    assert result["status"] in ["escalated", "pending"]

runner.test("Escalate to human", test_escalate_ticket)

# ============================================================================
# INTEGRATION TESTS
# ============================================================================

print("\n" + "="*70)
print("INTEGRATION TESTS: Complete Workflows")
print("="*70)

print("\n[WORKFLOW 1: Happy Path - KB Solution]")

def test_happy_path_workflow():
    """Complete flow: Validate → Score → Analyze → Classify → Plan → Evaluate"""
    ticket = create_ticket(
        "WF001",
        "How to reset password",
        "I forgot my password and need to reset it",
        client_name="John Doe",
        category="authentication"
    )
    
    # Step 1: Validate
    validation = validate_ticket(ticket)
    assert validation["valid"] == True
    
    # Step 2: Score
    score = score_ticket(ticket)
    assert score["score"] > 0
    ticket.priority_score = score["score"]
    
    # Step 3: Analyze
    analysis = analyze_and_reformulate_with_validation(ticket)
    assert "reformulation" in analysis
    ticket.keywords = analysis.get("keywords", [])
    ticket.reformulation = analysis.get("reformulation", "")
    
    # Step 4: Classify
    classification = classify_unified(ticket)
    assert classification.primary_category == "authentification"
    ticket.classification = classification
    
    # Step 5: Plan
    plan = plan_ticket_resolution(ticket)
    assert plan.resolution_path in ["kb_retrieval", "escalation"]
    
    # Step 6: Evaluate (simulating KB solution)
    evaluation = evaluate(
        ticket,
        "Click 'Forgot Password' on the login page",
        kb_confident=True,
        kb_limit_reached=False
    )
    assert evaluation["confidence"] > 0.6
    
    # Step 7: Compose response
    email = compose_response(ticket, "Click 'Forgot Password'", evaluation)
    assert len(email) > 0

runner.test("Happy path workflow (7 steps)", test_happy_path_workflow)

print("\n[WORKFLOW 2: Escalation Path - Critical Issue]")

def test_escalation_workflow():
    """Complete flow: Validate → Score (high) → Classify (critical) → Escalate"""
    ticket = create_ticket(
        "WF002",
        "CRITICAL: System down",
        "Production system crashed. Zero users can access."
    )
    
    # Step 1: Validate
    validation = validate_ticket(ticket)
    assert validation["valid"] == True
    
    # Step 2: Score
    score = score_ticket(ticket)
    assert score["score"] >= 70  # Critical should score high
    
    # Step 3: Classify
    classification = classify_unified(ticket)
    assert classification.severity in ["critical", "high"]
    ticket.classification = classification
    
    # Step 4: Plan (should escalate)
    plan = plan_ticket_resolution(ticket)
    assert plan.resolution_path == "escalation"
    
    # Step 5: Escalate
    escalation = escalate_ticket(ticket, "Critical severity", {})
    assert "escalation_id" in escalation

runner.test("Escalation workflow (critical path)", test_escalation_workflow)

print("\n[WORKFLOW 3: Feedback Loop]")

def test_feedback_workflow():
    """Feedback loop: Negative feedback → Retry/Escalate"""
    ticket = create_ticket(
        "WF003",
        "Something not working",
        "Error when uploading file"
    )
    
    # Initial solution (low confidence)
    solution_text = "Try clearing cache"
    evaluation = evaluate(
        ticket,
        solution_text,
        kb_confident=False,
        kb_limit_reached=False
    )
    
    # Compose email
    email = compose_response(ticket, solution_text, evaluation)
    assert len(email) > 0
    
    # Receive negative feedback
    feedback = {
        "sentiment": "negative",
        "helpful": False,
        "comment": "Still not working"
    }
    
    # Handle feedback
    result = handle_feedback(ticket, feedback)
    assert result["action"] in ["retry", "escalate"]

runner.test("Feedback loop (negative → action)", test_feedback_workflow)

# ============================================================================
# CONSISTENCY TESTS
# ============================================================================

print("\n" + "="*70)
print("CONSISTENCY TESTS: Cross-Agent Validation")
print("="*70)

print("\n[CONSISTENCY: Score & Classification Alignment]")

def test_score_classification_alignment():
    """Verify scoring and classification produce consistent results."""
    # Critical issue
    critical_ticket = create_ticket(
        "CONS001",
        "CRITICAL: System Down",
        "Production completely unavailable"
    )
    
    critical_score = score_ticket(critical_ticket)
    critical_class = classify_unified(critical_ticket)
    
    assert critical_score["score"] >= 70, "Critical should score ≥70"
    assert critical_class.severity in ["critical", "high"], "Should classify as critical"
    
    # Low priority
    low_ticket = create_ticket(
        "CONS002",
        "UI suggestion",
        "Small color improvement",
        category="feature_request"
    )
    
    low_score = score_ticket(low_ticket)
    low_class = classify_unified(low_ticket)
    
    assert low_score["score"] <= 50, "Low should score ≤50"
    assert low_class.severity in ["low", "medium"], "Should not be critical"

runner.test("Score & classification alignment", test_score_classification_alignment)

print("\n[CONSISTENCY: Reformulation Quality]")

def test_reformulation_consistency():
    """Verify reformulations contain key problem terms."""
    # Password issue
    ticket1 = create_ticket(
        "CONS003",
        "Can't login",
        "Password stopped working after update"
    )
    result1 = analyze_and_reformulate_with_validation(ticket1)
    reform1 = result1["reformulation"].lower()
    assert any(w in reform1 for w in ["password", "reset", "login"]), \
        f"Should mention password/login: {reform1}"
    
    # Billing issue
    ticket2 = create_ticket(
        "CONS004",
        "Overcharged",
        "Billed twice for subscription",
        category="billing"
    )
    result2 = analyze_and_reformulate_with_validation(ticket2)
    reform2 = result2["reformulation"].lower()
    assert any(w in reform2 for w in ["charge", "bill", "payment", "invoice"]), \
        f"Should mention billing terms: {reform2}"

runner.test("Reformulation consistency", test_reformulation_consistency)

# ============================================================================
# PRINT SUMMARY
# ============================================================================

success = runner.summary()

if success:
    print(f"\n✅ ALL TESTS PASSED! System is production-ready.")
    sys.exit(0)
else:
    print(f"\n⚠️  Some tests failed. Review errors above.")
    sys.exit(1)
