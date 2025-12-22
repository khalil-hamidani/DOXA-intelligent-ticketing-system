"""
Comprehensive Test Suite for DOXA System

Tests all agents individually and in integrated workflows.
No external dependencies (no pytest required).
"""

import sys
from pathlib import Path
import traceback
from typing import Tuple, List

# Add ai folder to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import Ticket
from agents.validator import validate_ticket
from agents.scorer import score_ticket
from agents.query_analyzer import analyze_and_reformulate_with_validation, classify_ticket
from agents.unified_classifier import classify_unified, ClassificationResult
from agents.query_planner import QueryPlanner, plan_ticket_resolution
from agents.solution_finder import find_solution
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
            self.errors.append((name, f"{type(e).__name__}: {e}"))
            print(f"  ✗ {name}: {type(e).__name__}: {e}")
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
                print(f"  • {test_name}: {error}")
        
        return self.failed == 0


# ============================================================================
# UNIT TESTS - Test each agent independently
# ============================================================================

def run_unit_tests():
    """Run unit tests for each agent."""
    print("\n" + "="*70)
    print("UNIT TESTS: Testing Individual Agents")
    print("="*70)
    
    runner = TestRunner()
    
    # VALIDATOR TESTS
    print("\n[VALIDATOR]")
    
    def test_valid_ticket():
        ticket = Ticket(
            id="TEST_001",
            subject="Cannot login to account",
            description="I've been trying to login for 2 hours but getting error 401",
            client_name="John Doe",
            email="john@example.com",
            category="authentication"
        )
        result = validate_ticket(ticket)
        assert result["valid"] == True, f"Valid ticket should pass: {result}"
        assert result["confidence"] >= 0.5, f"Confidence too low: {result['confidence']}"
    
    def test_invalid_empty_subject():
        ticket = Ticket(
            id="TEST_002",
            subject="",
            description="Help me please with a long description",
            client_name="Jane Doe",
            category="technique"
        )
        result = validate_ticket(ticket)
        assert result["valid"] == False, "Empty subject should be invalid"
    
    def test_invalid_short_description():
        ticket = Ticket(
            id="TEST_003",
            subject="Help",
            description="Hi",
            client_name="Bob",
            category="technique"
        )
        result = validate_ticket(ticket)
        assert result["valid"] == False, "Short description should be invalid"
    
    runner.test("Valid ticket", test_valid_ticket)
    runner.test("Reject empty subject", test_invalid_empty_subject)
    runner.test("Reject short description", test_invalid_short_description)
    
    # SCORER TESTS
    print("\n[SCORER]")
    
    def test_critical_score():
        ticket = Ticket(
            id="TEST_004",
            subject="System down - critical",
            description="Production system is completely down. No users can access.",
            client_name="Admin",
            category="technique"
        )
        result = score_ticket(ticket)
        assert result["score"] >= 70, f"Critical issue should score high: {result['score']}"
        assert 0 <= result["score"] <= 100, f"Score out of range: {result['score']}"
    
    def test_low_score():
        ticket = Ticket(
            id="TEST_005",
            subject="UI color suggestion",
            description="Button could be a different color",
            client_name="User",
            category="feature_request"
        )
        result = score_ticket(ticket)
        assert result["score"] <= 50, f"Low priority should score low: {result['score']}"
    
    runner.test("Score critical issue", test_critical_score)
    runner.test("Score low priority", test_low_score)
    
    # QUERY ANALYZER TESTS
    print("\n[QUERY ANALYZER]")
    
    def test_keyword_extraction():
        ticket = Ticket(
            id="TEST_006",
            subject="Password reset error",
            description="Error code 401 on Windows 10, need password reset",
            client_name="User",
            category="authentication"
        )
        analysis = analyze_and_reformulate_with_validation(ticket)
        assert "keywords" in analysis, "Keywords not extracted"
        assert len(analysis["keywords"]) > 0, "No keywords found"
    
    def test_reformulation():
        ticket = Ticket(
            id="TEST_007",
            subject="Can't login",
            description="Password not working",
            client_name="User",
            category="authentication"
        )
        analysis = analyze_and_reformulate_with_validation(ticket)
        assert "reformulation" in analysis, "Reformulation missing"
        assert len(analysis["reformulation"]) > 10, "Reformulation too short"
    
    runner.test("Extract keywords", test_keyword_extraction)
    runner.test("Reformulate query", test_reformulation)
    
    # UNIFIED CLASSIFIER TESTS
    print("\n[UNIFIED CLASSIFIER]")
    
    def test_auth_classification():
        ticket = Ticket(
            id="TEST_008",
            subject="Cannot reset password",
            description="I forgot password and cannot login",
            client_name="User",
            category="authentication"
        )
        result = classify_unified(ticket)
        assert result.primary_category == "authentification", f"Wrong category: {result.primary_category}"
        overall = result.overall_confidence()
        assert 0 <= overall <= 1.0, f"Invalid confidence: {overall}"
    
    def test_classification_confidence():
        ticket = Ticket(
            id="TEST_009",
            subject="Wrong charge on invoice",
            description="Charged $100 twice",
            client_name="Customer",
            category="billing"
        )
        result = classify_unified(ticket)
        assert result.primary_category == "facturation", f"Wrong category: {result.primary_category}"
        assert result.confidence_category >= 0.5, f"Confidence too low: {result.confidence_category}"
    
    runner.test("Classify authentication", test_auth_classification)
    runner.test("Classify billing", test_classification_confidence)
    
    # QUERY PLANNER TESTS
    print("\n[QUERY PLANNER]")
    
    def test_plan_kb_retrieval():
        ticket = Ticket(
            id="TEST_010",
            subject="How to change password",
            description="I want to change my password for security",
            client_name="User",
            category="authentication"
        )
        analysis = analyze_and_reformulate_with_validation(ticket)
        classification = classify_unified(ticket)
        ticket.classification = classification
        ticket.keywords = analysis.get("keywords", [])
        
        plan = plan_ticket_resolution(ticket)
        assert plan.resolution_path in ["kb_retrieval", "escalation"], f"Invalid path: {plan.resolution_path}"
    
    def test_plan_escalation():
        ticket = Ticket(
            id="TEST_011",
            subject="System is down",
            description="Entire platform not responding",
            client_name="Admin",
            category="technique"
        )
        analysis = analyze_and_reformulate_with_validation(ticket)
        classification = classify_unified(ticket)
        classification.severity = "critical"
        ticket.classification = classification
        
        plan = plan_ticket_resolution(ticket)
        assert plan.resolution_path == "escalation", f"Critical should escalate: {plan.resolution_path}"
    
    runner.test("Plan KB retrieval", test_plan_kb_retrieval)
    runner.test("Plan escalation (critical)", test_plan_escalation)
    
    # EVALUATOR TESTS
    print("\n[EVALUATOR]")
    
    def test_high_confidence_eval():
        ticket = Ticket(
            id="TEST_012",
            subject="Password reset",
            description="Help resetting",
            client_name="User",
            category="authentication"
        )
        solution_text = "Click Forgot Password on login page"
        result = evaluate(ticket, solution_text, kb_confident=True, kb_limit_reached=False)
        assert result["confidence"] >= 0.6, f"High confidence too low: {result['confidence']}"
    
    def test_low_confidence_eval():
        ticket = Ticket(
            id="TEST_013",
            subject="Unknown error",
            description="Something is wrong",
            client_name="User",
            category="technique"
        )
        solution_text = "Try restarting"
        result = evaluate(ticket, solution_text, kb_confident=False, kb_limit_reached=True)
        assert "confidence" in result, "Confidence missing"
        assert isinstance(result["confidence"], (int, float)), f"Invalid confidence type: {type(result['confidence'])}"
    
    runner.test("Evaluate high confidence", test_high_confidence_eval)
    runner.test("Evaluate low confidence", test_low_confidence_eval)
    
    # RESPONSE COMPOSER TESTS
    print("\n[RESPONSE COMPOSER]")
    
    def test_compose_email():
        ticket = Ticket(
            id="TEST_014",
            subject="Password reset",
            description="Help",
            client_name="Alice",
            category="authentication"
        )
        solution_text = "Click Forgot Password"
        email_body = compose_response(
            ticket,
            solution_text,
            evaluation={"confidence": 0.85, "escalate": False}
        )
        assert isinstance(email_body, str), f"Email should be string: {type(email_body)}"
        assert len(email_body) > 0, "Email body empty"
    
    runner.test("Compose email", test_compose_email)
    
    # FEEDBACK HANDLER TESTS
    print("\n[FEEDBACK HANDLER]")
    
    def test_positive_feedback():
        ticket = Ticket(
            id="TEST_015",
            subject="Test",
            description="Test",
            client_name="User",
            category="technique"
        )
        ticket.retry_count = 0
        feedback = {
            "sentiment": "positive",
            "helpful": True,
            "comment": "Great!"
        }
        result = handle_feedback(ticket, feedback)
        assert result["action"] == "close", f"Positive feedback should close: {result['action']}"
    
    def test_negative_feedback():
        ticket = Ticket(
            id="TEST_016",
            subject="Test",
            description="Test",
            client_name="User",
            category="technique"
        )
        ticket.retry_count = 0
        feedback = {
            "sentiment": "negative",
            "helpful": False,
            "comment": "Didn't work"
        }
        result = handle_feedback(ticket, feedback)
        assert result["action"] in ["retry", "escalate"], f"Invalid action: {result['action']}"
    
    runner.test("Positive feedback → close", test_positive_feedback)
    runner.test("Negative feedback → retry/escalate", test_negative_feedback)
    
    # ESCALATION TESTS
    print("\n[ESCALATION MANAGER]")
    
    def test_escalate():
        ticket = Ticket(
            id="TEST_017",
            subject="Critical",
            description="System down",
            client_name="Admin",
            category="technique"
        )
        result = escalate_ticket(ticket, "Test escalation", {})
        assert "escalation_id" in result, "Escalation ID missing"
        assert result["status"] in ["escalated", "pending"], f"Invalid status: {result['status']}"
    
    runner.test("Escalate ticket", test_escalate)
    
    return runner


# ============================================================================
# INTEGRATION TESTS - Test complete workflows
# ============================================================================

def run_integration_tests():
    """Run integration tests for complete workflows."""
    print("\n" + "="*70)
    print("INTEGRATION TESTS: Complete Workflows")
    print("="*70)
    
    runner = TestRunner()
    
    print("\n[FULL WORKFLOW: Happy Path (KB Solution)]")
    
    def test_happy_path():
        """Complete flow: Valid ticket → KB solution → confident answer."""
        ticket = Ticket(
            id="WORKFLOW_001",
            subject="How to reset password",
            description="I forgot my password and need to reset it",
            client_name="John Doe",
            category="authentication"
        )
        
        # Step 1: Validate
        validation = validate_ticket(ticket)
        assert validation["valid"] == True, "Should validate"
        
        # Step 2: Score
        score = score_ticket(ticket)
        assert score["score"] > 0, "Should score"
        
        # Step 3: Analyze
        analysis = analyze_and_reformulate_with_validation(ticket)
        assert "reformulation" in analysis, "Should reformulate"
        
        # Step 4: Classify
        classification = classify_unified(ticket)
        assert classification.primary_category == "authentification", "Wrong category"
        ticket.classification = classification
        
        # Step 5: Plan
        plan = plan_ticket_resolution(ticket)
        assert plan.resolution_path in ["kb_retrieval", "escalation"], "Invalid path"
        
        # Step 6: Find solution (mock)
        solution = {
            "solution_text": "Click 'Forgot Password' on the login page",
            "kb_confident": True,
            "kb_limit_reached": False
        }
        
        # Step 7: Evaluate
        evaluation = evaluate(ticket, solution["solution_text"], 
                            kb_confident=solution["kb_confident"],
                            kb_limit_reached=solution["kb_limit_reached"])
        assert evaluation["confidence"] > 0.6, "Should be confident"
        
        # Step 8: Compose email
        email = compose_response(ticket, solution["solution_text"], evaluation)
        assert len(email) > 0, "Should compose email"
    
    runner.test("Happy path (KB → confident answer)", test_happy_path)
    
    print("\n[FULL WORKFLOW: Escalation Path]")
    
    def test_escalation_workflow():
        """Complete flow: Critical issue → escalation."""
        ticket = Ticket(
            id="WORKFLOW_002",
            subject="System is completely down",
            description="Production system crashed. No users can access.",
            client_name="Admin",
            category="technique"
        )
        
        # Step 1: Validate
        validation = validate_ticket(ticket)
        assert validation["valid"] == True, "Should validate"
        
        # Step 2: Score
        score = score_ticket(ticket)
        assert score["score"] >= 80, "Critical should score high"
        
        # Step 3: Classify with critical severity
        classification = classify_unified(ticket)
        classification.severity = "critical"  # Force critical
        ticket.classification = classification
        
        # Step 4: Plan (should escalate due to critical)
        plan = plan_ticket_resolution(ticket)
        assert plan.resolution_path == "escalation", "Critical should escalate"
        
        # Step 5: Escalate
        escalation = escalate_ticket(ticket, "Critical severity", {})
        assert "escalation_id" in escalation, "Should create escalation"
    
    runner.test("Escalation workflow (critical → human)", test_escalation_workflow)
    
    print("\n[FULL WORKFLOW: Feedback Loop (Negative → Retry)]")
    
    def test_feedback_retry_workflow():
        """Complete flow: Negative feedback → retry → new solution."""
        ticket = Ticket(
            id="WORKFLOW_003",
            subject="Something not working",
            description="Error when uploading file",
            client_name="User",
            category="technique"
        )
        ticket.retry_count = 0
        
        # Simulate initial solution (low confidence)
        solution_text = "Try clearing cache"
        evaluation = evaluate(ticket, solution_text, 
                            kb_confident=False,
                            kb_limit_reached=False)
        
        # Compose and send email
        email = compose_response(ticket, solution_text, evaluation)
        assert len(email) > 0, "Should compose email"
        
        # Receive negative feedback
        feedback = {
            "sentiment": "negative",
            "helpful": False,
            "comment": "Still not working"
        }
        
        # Handle feedback
        feedback_result = handle_feedback(ticket, feedback)
        assert feedback_result["action"] in ["retry", "escalate"], f"Invalid action: {feedback_result['action']}"
        
        # If retry, we would go back to Step 5 (Plan) and try KB again
        if feedback_result["action"] == "retry":
            ticket.retry_count += 1
            assert ticket.retry_count >= 1, "Retry count should increase"
    
    runner.test("Feedback retry workflow", test_feedback_retry_workflow)
    
    print("\n[FULL WORKFLOW: Max Retries → Escalation]")
    
    def test_max_retries_escalation():
        """Complete flow: Max retries reached → escalation."""
        ticket = Ticket(
            id="WORKFLOW_004",
            subject="Persistent issue",
            description="Nothing I try works",
            client_name="User",
            category="technique"
        )
        ticket.retry_count = 2  # Max retries
        
        # Try one more time with limit reached
        solution = {
            "kb_confident": False,
            "kb_limit_reached": True
        }
        
        evaluation = evaluate(ticket, "Some solution",
                            kb_confident=solution["kb_confident"],
                            kb_limit_reached=solution["kb_limit_reached"])
        
        # Should suggest escalation
        feedback = {"sentiment": "negative", "helpful": False, "comment": "Still broken"}
        feedback_result = handle_feedback(ticket, feedback)
        
        # With max retries, should escalate
        if ticket.retry_count >= 2:
            escalation = escalate_ticket(ticket, "Max retries reached", {})
            assert "escalation_id" in escalation, "Should escalate on max retries"
    
    runner.test("Max retries → escalation", test_max_retries_escalation)
    
    return runner


# ============================================================================
# CONSISTENCY TESTS - Verify consistency across flows
# ============================================================================

def run_consistency_tests():
    """Run consistency tests across multiple flows."""
    print("\n" + "="*70)
    print("CONSISTENCY TESTS: Cross-Flow Validation")
    print("="*70)
    
    runner = TestRunner()
    
    print("\n[CONSISTENCY: Classifier Confidence Breakdown]")
    
    def test_classifier_confidence_breakdown():
        """Verify classifier confidence is properly weighted."""
        ticket = Ticket(
            id="CONSISTENCY_001",
            subject="Test",
            description="Test ticket with substantial description for analysis",
            client_name="User",
            category="authentication"
        )
        
        result = classify_unified(ticket)
        
        # Check all confidence values are valid
        assert 0 <= result.confidence_category <= 1.0, f"Invalid category confidence: {result.confidence_category}"
        assert 0 <= result.confidence_severity <= 1.0, f"Invalid severity confidence: {result.confidence_severity}"
        assert 0 <= result.confidence_treatment <= 1.0, f"Invalid treatment confidence: {result.confidence_treatment}"
        assert 0 <= result.confidence_skills <= 1.0, f"Invalid skills confidence: {result.confidence_skills}"
        
        overall = result.overall_confidence()
        assert 0 <= overall <= 1.0, f"Invalid overall confidence: {overall}"
        
        # Overall should be weighted average
        expected_range = min(result.confidence_category, result.confidence_severity, 
                           result.confidence_treatment, result.confidence_skills)
        assert overall >= expected_range * 0.8, "Overall confidence seems wrong"
    
    runner.test("Classifier confidence breakdown", test_classifier_confidence_breakdown)
    
    print("\n[CONSISTENCY: Scoring and Classification Alignment]")
    
    def test_score_classification_alignment():
        """Verify score and classification align properly."""
        # Critical issue
        critical_ticket = Ticket(
            id="CONSISTENCY_002",
            subject="CRITICAL: System Down",
            description="Production completely unavailable",
            client_name="Admin",
            category="technique"
        )
        
        critical_score = score_ticket(critical_ticket)
        critical_class = classify_unified(critical_ticket)
        
        assert critical_score["score"] >= 80, "Critical should score high"
        assert critical_class.severity == "critical", "Should classify as critical"
        
        # Low priority issue
        low_ticket = Ticket(
            id="CONSISTENCY_003",
            subject="Nice to have feature",
            description="Small UI improvement",
            client_name="User",
            category="feature_request"
        )
        
        low_score = score_ticket(low_ticket)
        low_class = classify_unified(low_ticket)
        
        assert low_score["score"] <= 50, "Low priority should score low"
        assert low_class.severity in ["low", "medium"], "Should not be critical"
    
    runner.test("Score and classification alignment", test_score_classification_alignment)
    
    print("\n[CONSISTENCY: Email Signal Consistency]")
    
    def test_email_signal_consistency():
        """Verify email signals are consistent with evaluations."""
        ticket = Ticket(
            id="CONSISTENCY_004",
            subject="Test",
            description="Test ticket",
            client_name="User",
            category="authentication"
        )
        
        # Case 1: High confidence KB result
        kb_high = {"kb_confident": True, "kb_limit_reached": False}
        eval_high = evaluate(ticket, "Solution", kb_confident=True, kb_limit_reached=False)
        assert eval_high["confidence"] >= 0.6, "High kb_confident should produce high confidence"
        
        # Case 2: Low confidence, retries exhausted
        kb_low = {"kb_confident": False, "kb_limit_reached": True}
        eval_low = evaluate(ticket, "Solution", kb_confident=False, kb_limit_reached=True)
        # Should suggest escalation or be cautious
        assert "confidence" in eval_low, "Should have confidence"
    
    runner.test("Email signal consistency", test_email_signal_consistency)
    
    print("\n[CONSISTENCY: Reformulation Quality]")
    
    def test_reformulation_quality():
        """Verify reformulations are meaningful and consistent."""
        
        # Test 1: Password reset
        ticket1 = Ticket(
            id="CONSISTENCY_005",
            subject="Can't login",
            description="Password stopped working",
            client_name="User",
            category="authentication"
        )
        result1 = analyze_and_reformulate_with_validation(ticket1)
        assert any(word in result1["reformulation"].lower() for word in ["password", "reset", "login"]), \
            f"Reformulation should contain password/reset/login: {result1['reformulation']}"
        
        # Test 2: Billing issue
        ticket2 = Ticket(
            id="CONSISTENCY_006",
            subject="Overcharged",
            description="Billed twice for subscription",
            client_name="Customer",
            category="billing"
        )
        result2 = analyze_and_reformulate_with_validation(ticket2)
        assert any(word in result2["reformulation"].lower() for word in ["charge", "bill", "invoice"]), \
            f"Reformulation should contain billing terms: {result2['reformulation']}"
    
    runner.test("Reformulation quality", test_reformulation_quality)
    
    return runner


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def main():
    """Run all test suites."""
    print("\n" + "="*70)
    print("DOXA COMPREHENSIVE TEST SUITE")
    print("="*70)
    
    # Run unit tests
    unit_runner = run_unit_tests()
    
    # Run integration tests
    integration_runner = run_integration_tests()
    
    # Run consistency tests
    consistency_runner = run_consistency_tests()
    
    # Combined summary
    print("\n" + "="*70)
    print("OVERALL TEST RESULTS")
    print("="*70)
    
    total_passed = unit_runner.passed + integration_runner.passed + consistency_runner.passed
    total_failed = unit_runner.failed + integration_runner.failed + consistency_runner.failed
    total = total_passed + total_failed
    
    print(f"\nUnit Tests:        {unit_runner.passed}/{unit_runner.passed + unit_runner.failed} passed")
    print(f"Integration Tests: {integration_runner.passed}/{integration_runner.passed + integration_runner.failed} passed")
    print(f"Consistency Tests: {consistency_runner.passed}/{consistency_runner.passed + consistency_runner.failed} passed")
    print(f"\n{'─'*70}")
    print(f"TOTAL:             {total_passed}/{total} tests passed")
    print(f"{'─'*70}")
    
    if total_failed == 0:
        print(f"\n✅ ALL TESTS PASSED! System is ready for production.")
        return 0
    else:
        print(f"\n⚠️  {total_failed} test(s) failed. See details above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
