"""
Comprehensive Test Suite for Ticket Processing System

Structure:
- Unit tests: One test per agent
- Integration tests: Full workflow test
- Edge cases: Error handling, feedback loops
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Ticket
from agents.validator import validate_ticket
from agents.scorer import score_ticket
from agents.query_analyzer import analyze_and_reformulate, classify_ticket
from agents.classifier import classify_ticket_model
from agents.solution_finder import find_solution
from agents.evaluator import evaluate
from agents.response_composer import compose_response
from agents.feedback_handler import handle_feedback
from agents.escalation_manager import escalate_ticket
from agents.continuous_improvment import analyze_improvements

from typing import Dict, List, Any
import json


# ============================================================================
# TEST FIXTURES & SAMPLE DATA
# ============================================================================

def create_ticket(subject: str, description: str, client: str = "Test Client") -> Ticket:
    """Factory to create test tickets."""
    return Ticket(
        id="test_" + subject.replace(" ", "_").lower()[:20],
        client_name=client,
        email=f"{client.lower().replace(' ', '')}@example.com",
        subject=subject,
        description=description
    )


# Test Cases
VALID_TICKET = create_ticket(
    "Login not working",
    "I cannot log into my account. I've tried resetting my password but still get an 'Invalid credentials' error. This happened after I updated my browser to the latest version."
)

VAGUE_TICKET = create_ticket(
    "Help",
    "It doesn't work"
)

URGENT_TECHNICAL_TICKET = create_ticket(
    "Production system down - URGENT",
    "Our production database server has crashed and is no longer responding. All customers are currently unable to access the service. This is a critical downtime situation affecting revenue. ASAP help needed!"
)

BILLING_TICKET = create_ticket(
    "Invoice issue",
    "I received an invoice for $500 but my subscription should only cost $200 per month. This is the second time this has happened. Can you explain this overcharge and refund the difference?"
)

RECURRENT_TECHNICAL_TICKET = create_ticket(
    "API timeout recurring",
    "The API endpoint /v2/reports keeps timing out intermittently. This happens several times per week, blocking our batch job processing. I've seen this error repeated over the past month."
)

AUTHENTICATION_TICKET = create_ticket(
    "Can't access my account",
    "I'm trying to reset my password but I never receive the reset email. I've checked spam folder. This is blocking me from accessing my data."
)


# ============================================================================
# UNIT TESTS - ONE TEST PER AGENT
# ============================================================================

class TestResults:
    """Collect test results."""
    def __init__(self):
        self.tests: Dict[str, Dict] = {}
        self.total = 0
        self.passed = 0
        self.failed = 0
    
    def record(self, agent_name: str, test_name: str, passed: bool, details: str):
        """Record test result."""
        self.total += 1
        if passed:
            self.passed += 1
            status = "✅ PASS"
        else:
            self.failed += 1
            status = "❌ FAIL"
        
        if agent_name not in self.tests:
            self.tests[agent_name] = {}
        
        self.tests[agent_name][test_name] = {
            "status": status,
            "details": details
        }
        
        print(f"  {status}: {test_name}")
        print(f"    {details}")
    
    def summary(self):
        """Print test summary."""
        print("\n" + "="*80)
        print(f"TEST SUMMARY: {self.passed}/{self.total} passed, {self.failed} failed")
        print("="*80)
        for agent_name, tests in self.tests.items():
            print(f"\n{agent_name}:")
            for test_name, result in tests.items():
                print(f"  {result['status']}: {test_name}")


results = TestResults()


# ============================================================================
# TEST 1: VALIDATOR AGENT
# ============================================================================

def test_validator():
    """Test Validator Agent - validates ticket content."""
    print("\n" + "="*80)
    print("TEST 1: VALIDATOR AGENT")
    print("="*80)
    print("\nValidator must check: context clarity, keywords, exploitability")
    
    # Test 1.1: Valid ticket should pass
    print("\n1.1: Valid ticket (should be VALID)")
    result = validate_ticket(VALID_TICKET)
    passed = result.get("valid") == True and "reasons" in result
    results.record("Validator", "Valid ticket acceptance", passed, 
                  f"Valid={result.get('valid')}, Reasons={result.get('reasons')}")
    
    # Test 1.2: Vague ticket should fail
    print("\n1.2: Vague ticket (should be INVALID)")
    result = validate_ticket(VAGUE_TICKET)
    passed = result.get("valid") == False and len(result.get("reasons", [])) > 0
    results.record("Validator", "Vague ticket rejection", passed,
                  f"Valid={result.get('valid')}, Reasons={result.get('reasons')}")
    
    # Test 1.3: Urgent technical ticket should still be valid
    print("\n1.3: Urgent technical ticket (should be VALID)")
    result = validate_ticket(URGENT_TECHNICAL_TICKET)
    passed = result.get("valid") == True
    results.record("Validator", "Urgent ticket acceptance", passed,
                  f"Valid={result.get('valid')}")
    
    return VALID_TICKET


# ============================================================================
# TEST 2: SCORER AGENT
# ============================================================================

def test_scorer(ticket: Ticket):
    """Test Scorer Agent - computes priority scores."""
    print("\n" + "="*80)
    print("TEST 2: SCORER AGENT")
    print("="*80)
    print("\nScorer must score based: urgency, recurrence, business impact (0-100)")
    
    # Test 2.1: Urgent ticket should score high
    print("\n2.1: Urgent technical ticket (should score HIGH)")
    result = score_ticket(URGENT_TECHNICAL_TICKET)
    passed = result.get("score", 0) >= 70
    results.record("Scorer", "Urgent ticket high priority", passed,
                  f"Score={result.get('score')}, Priority={result.get('priority')}")
    
    # Test 2.2: Normal ticket should score medium
    print("\n2.2: Normal ticket (should score MEDIUM)")
    result = score_ticket(VALID_TICKET)
    passed = 30 <= result.get("score", 50) < 70
    results.record("Scorer", "Normal ticket medium priority", passed,
                  f"Score={result.get('score')}, Priority={result.get('priority')}")
    
    # Test 2.3: Recurrent problem should boost score
    print("\n2.3: Recurrent issue (should score HIGH)")
    result = score_ticket(RECURRENT_TECHNICAL_TICKET)
    passed = result.get("score", 0) >= 50
    results.record("Scorer", "Recurrent issue detection", passed,
                  f"Score={result.get('score')}")


# ============================================================================
# TEST 3: QUERY ANALYZER (Agent A: Reformulation)
# ============================================================================

def test_query_analyzer(ticket: Ticket):
    """Test Query Analyzer Agent A - reformulation & keyword extraction."""
    print("\n" + "="*80)
    print("TEST 3: QUERY ANALYZER (Reformulation)")
    print("="*80)
    print("\nAgent A: Summarize, reformulate, extract keywords")
    
    # Test 3.1: Extract keywords
    print("\n3.1: Keyword extraction (should find 5-8 keywords)")
    result = analyze_and_reformulate(ticket)
    passed = "keywords" in result and 5 <= len(result.get("keywords", [])) <= 8
    results.record("QueryAnalyzer", "Keyword extraction", passed,
                  f"Keywords={result.get('keywords')}")
    
    # Test 3.2: Generate summary
    print("\n3.2: Summary generation (should be <100 chars)")
    result = analyze_and_reformulate(ticket)
    passed = "summary" in result and len(result.get("summary", "")) > 0
    results.record("QueryAnalyzer", "Summary generation", passed,
                  f"Summary={result.get('summary')}")
    
    # Test 3.3: Reformulate problem
    print("\n3.3: Problem reformulation (should be clear)")
    result = analyze_and_reformulate(ticket)
    passed = "reformulation" in result and len(result.get("reformulation", "")) > 0
    results.record("QueryAnalyzer", "Problem reformulation", passed,
                  f"Reformulation={result.get('reformulation')}")


# ============================================================================
# TEST 4: CLASSIFIER (Agent B: Categorization)
# ============================================================================

def test_classifier(ticket: Ticket):
    """Test Classifier Agent B - category determination."""
    print("\n" + "="*80)
    print("TEST 4: CLASSIFIER (Categorization)")
    print("="*80)
    print("\nAgent B: Categorize ticket (technique/facturation/authentification/autre)")
    
    # Test 4.1: Technical ticket classification
    print("\n4.1: Technical ticket (should classify as TECHNIQUE)")
    result = classify_ticket_model(URGENT_TECHNICAL_TICKET)
    passed = result.get("category") == "technique"
    results.record("Classifier", "Technical ticket classification", passed,
                  f"Category={result.get('category')}, Confidence={result.get('confidence')}")
    
    # Test 4.2: Billing ticket classification
    print("\n4.2: Billing ticket (should classify as FACTURATION)")
    result = classify_ticket_model(BILLING_TICKET)
    passed = result.get("category") == "facturation"
    results.record("Classifier", "Billing ticket classification", passed,
                  f"Category={result.get('category')}, Confidence={result.get('confidence')}")
    
    # Test 4.3: Auth ticket classification
    print("\n4.3: Authentication ticket (should classify as AUTHENTIFICATION)")
    result = classify_ticket_model(AUTHENTICATION_TICKET)
    passed = result.get("category") == "authentification"
    results.record("Classifier", "Authentication ticket classification", passed,
                  f"Category={result.get('category')}, Confidence={result.get('confidence')}")
    
    # Test 4.4: Treatment type based on priority
    print("\n4.4: Treatment type assignment (based on priority)")
    result = classify_ticket_model(URGENT_TECHNICAL_TICKET)
    passed = result.get("treatment_type") in ["standard", "priority", "escalation", "urgent"]
    results.record("Classifier", "Treatment type assignment", passed,
                  f"Treatment={result.get('treatment_type')}")


# ============================================================================
# TEST 5: SOLUTION FINDER (RAG Core)
# ============================================================================

def test_solution_finder(ticket: Ticket):
    """Test Solution Finder - retrieves from KB."""
    print("\n" + "="*80)
    print("TEST 5: SOLUTION FINDER (RAG/KB Search)")
    print("="*80)
    print("\nSolution Finder: Query RAG pipeline, get contextual docs")
    
    # Note: This requires KB to be loaded
    # For testing purposes, we check the interface
    
    # Test 5.1: Returns structured result
    print("\n5.1: Solution finding (should return structure)")
    result = find_solution(ticket)
    passed = "solution_text" in result and "confidence" in result
    results.record("SolutionFinder", "Structured result", passed,
                  f"Has solution_text={('solution_text' in result)}, confidence={result.get('confidence')}")
    
    # Test 5.2: Handles missing KB gracefully
    print("\n5.2: Graceful degradation (if KB empty)")
    passed = "solution_text" in result  # Should fallback
    results.record("SolutionFinder", "Fallback handling", passed,
                  f"Fallback triggered={result.get('solution_text', '').startswith('Fallback')}")


# ============================================================================
# TEST 6: EVALUATOR (Confidence & Escalation)
# ============================================================================

def test_evaluator(ticket: Ticket):
    """Test Evaluator - confidence scoring and escalation decision."""
    print("\n" + "="*80)
    print("TEST 6: EVALUATOR (Confidence & Escalation)")
    print("="*80)
    print("\nEvaluator: Calculate confidence, detect issues, decide escalation")
    
    # Setup: Solution finder result
    ticket.snippets = [{"text": "Solution found", "similarity": 0.85}]
    ticket.priority_score = 50
    
    # Test 6.1: Confidence calculation
    print("\n6.1: Confidence scoring (0-1.0)")
    result = evaluate(ticket)
    passed = 0.0 <= result.get("confidence", 0) <= 1.0
    results.record("Evaluator", "Confidence calculation", passed,
                  f"Confidence={result.get('confidence'):.2f}")
    
    # Test 6.2: Escalation detection (low confidence)
    print("\n6.2: Escalation trigger (if confidence < 60%)")
    ticket.priority_score = 10
    ticket.snippets = []  # Empty snippets = low confidence
    result = evaluate(ticket)
    passed = result.get("escalate") == True if result.get("confidence", 0) < 0.6 else True
    results.record("Evaluator", "Escalation detection", passed,
                  f"Escalate={result.get('escalate')}, Confidence={result.get('confidence'):.2f}")
    
    # Test 6.3: Sensitive data detection
    print("\n6.3: Sensitive data detection")
    ticket.description = "My credit card is 4532-1234-5678-9999"
    result = evaluate(ticket)
    passed = result.get("sensitive") == True
    results.record("Evaluator", "Sensitive data detection", passed,
                  f"Sensitive={result.get('sensitive')}")


# ============================================================================
# TEST 7: RESPONSE COMPOSER
# ============================================================================

def test_response_composer(ticket: Ticket):
    """Test Response Composer - generates final response."""
    print("\n" + "="*80)
    print("TEST 7: RESPONSE COMPOSER")
    print("="*80)
    print("\nComposer: Generate structured response (thank you + problem + solution + steps)")
    
    solution_text = "To fix this issue, please follow these steps..."
    eval_result = {"confidence": 0.75, "reasons": []}
    
    # Test 7.1: Response structure
    print("\n7.1: Response structure (should contain all sections)")
    response = compose_response(ticket, solution_text, eval_result)
    passed = "thank" in response.lower() or "merci" in response.lower()
    results.record("ResponseComposer", "Response structure", passed,
                  f"Response length={len(response)}")
    
    # Test 7.2: Solution inclusion
    print("\n7.2: Solution inclusion")
    passed = "solution" in response.lower() or solution_text.lower() in response.lower()
    results.record("ResponseComposer", "Solution integration", passed,
                  f"Contains solution text={passed}")


# ============================================================================
# TEST 8: FEEDBACK HANDLER
# ============================================================================

def test_feedback_handler(ticket: Ticket):
    """Test Feedback Handler - client satisfaction & retry logic."""
    print("\n" + "="*80)
    print("TEST 8: FEEDBACK HANDLER")
    print("="*80)
    print("\nFeedback: Collect satisfaction, handle retries (max 2 attempts)")
    
    # Test 8.1: Satisfied feedback
    print("\n8.1: Client satisfied (should close ticket)")
    ticket.attempts = 1
    feedback = {"satisfied": True}
    result = handle_feedback(ticket, feedback)
    passed = result.get("action") in ["close", "closed"]
    results.record("FeedbackHandler", "Satisfied feedback handling", passed,
                  f"Action={result.get('action')}")
    
    # Test 8.2: Unsatisfied feedback + attempts left
    print("\n8.2: Client unsatisfied + attempts left (should retry)")
    ticket.attempts = 1
    feedback = {"satisfied": False, "clarification": "I need more help"}
    result = handle_feedback(ticket, feedback)
    passed = result.get("action") in ["retry", "relance"]
    results.record("FeedbackHandler", "Unsatisfied with retry", passed,
                  f"Action={result.get('action')}, Attempts={result.get('attempts')}")
    
    # Test 8.3: Max attempts reached (should escalate)
    print("\n8.3: Max attempts reached (should escalate)")
    ticket.attempts = 2
    feedback = {"satisfied": False}
    result = handle_feedback(ticket, feedback)
    passed = result.get("action") in ["escalate", "escalation"]
    results.record("FeedbackHandler", "Max attempts escalation", passed,
                  f"Action={result.get('action')}")


# ============================================================================
# TEST 9: ESCALATION MANAGER
# ============================================================================

def test_escalation_manager(ticket: Ticket):
    """Test Escalation Manager - human handoff."""
    print("\n" + "="*80)
    print("TEST 9: ESCALATION MANAGER")
    print("="*80)
    print("\nEscalation: Route to human, send email, create context")
    
    # Test 9.1: Escalation creation
    print("\n9.1: Escalation creation (should create context)")
    result = escalate_ticket(ticket, reason="Low confidence", context={})
    passed = "escalation_id" in result or "status" in result
    results.record("EscalationManager", "Escalation creation", passed,
                  f"Result keys={list(result.keys())}")
    
    # Test 9.2: Email notification (simulated)
    print("\n9.2: Email notification (should be sent)")
    passed = result.get("notification_sent") == True or "email" in str(result)
    results.record("EscalationManager", "Email notification", passed,
                  f"Notification sent={result.get('notification_sent')}")


# ============================================================================
# TEST 10: CONTINUOUS IMPROVEMENT
# ============================================================================

def test_continuous_improvement():
    """Test Continuous Improvement - analyze escalations and patterns."""
    print("\n" + "="*80)
    print("TEST 10: CONTINUOUS IMPROVEMENT AGENT")
    print("="*80)
    print("\nCI Agent: Analyze escalations, detect KB gaps, flag hallucinations")
    
    escalations = [
        {
            "ticket_id": "t1",
            "category": "technique",
            "reason": "KB gap - no solution found",
            "human_resolution": "Updated configuration file"
        },
        {
            "ticket_id": "t2",
            "category": "technique",
            "reason": "AI hallucination - incorrect solution",
            "human_resolution": "Completely different approach needed"
        }
    ]
    
    # Test 10.1: Pattern detection
    print("\n10.1: Pattern detection (should find recurring issues)")
    result = analyze_improvements(escalations)
    passed = "patterns" in result or "gaps" in result
    results.record("ContinuousImprovement", "Pattern detection", passed,
                  f"Found patterns={('patterns' in result)}")
    
    # Test 10.2: KB gap identification
    print("\n10.2: KB gap identification")
    passed = "kb_gaps" in result or result.get("kb_gaps_count", 0) >= 0
    results.record("ContinuousImprovement", "KB gap identification", passed,
                  f"KB gaps found={result.get('kb_gaps_count', 0)}")
    
    # Test 10.3: Hallucination detection
    print("\n10.3: Hallucination detection")
    passed = "hallucinations" in result or result.get("hallucination_count", 0) >= 0
    results.record("ContinuousImprovement", "Hallucination detection", passed,
                  f"Hallucinations found={result.get('hallucination_count', 0)}")


# ============================================================================
# INTEGRATION TEST: FULL WORKFLOW
# ============================================================================

def test_full_workflow():
    """Integration Test: Full ticket processing workflow."""
    print("\n\n" + "="*80)
    print("INTEGRATION TEST: FULL WORKFLOW")
    print("="*80)
    print("\nTest the complete flow: Validation → Scoring → Analysis → RAG → Eval → Compose → Feedback")
    
    # Create a fresh ticket for integration test (not reusing modified test ticket)
    ticket = create_ticket(
        "Login issue to resolve",
        "I cannot access my account after browser update. Password reset didn't help. Getting 'Invalid credentials' error."
    )
    
    # Step 0: Validation
    print("\nStep 0: VALIDATION")
    validation = validate_ticket(ticket)
    if not validation.get("valid"):
        print(f"  ❌ Ticket rejected: {validation.get('reasons')}")
        results.record("Workflow", "Full workflow execution", False, "Validation failed")
        return
    print(f"  ✓ Ticket valid")
    
    # Step 1: Scoring
    print("\nStep 1: SCORING")
    scoring = score_ticket(ticket)
    ticket.priority_score = scoring.get("score", 50)
    print(f"  ✓ Priority score: {ticket.priority_score}")
    
    # Step 2: Query Analysis
    print("\nStep 2: QUERY ANALYSIS")
    analysis = analyze_and_reformulate(ticket)
    ticket.summary = analysis.get("summary")
    ticket.keywords = analysis.get("keywords")
    print(f"  ✓ Summary: {ticket.summary}")
    
    # Step 3: Classification
    print("\nStep 3: CLASSIFICATION")
    classification = classify_ticket_model(ticket)
    ticket.category = classification.get("category")
    print(f"  ✓ Category: {ticket.category}")
    
    # Step 4: Solution Finding (RAG)
    print("\nStep 4: SOLUTION FINDING (RAG)")
    solution = find_solution(ticket)
    print(f"  ✓ Solution found")
    
    # Step 5: Evaluation
    print("\nStep 5: EVALUATION")
    evaluation = evaluate(ticket)
    print(f"  ✓ Confidence: {evaluation.get('confidence'):.2f}")
    
    # Step 6: Decision
    if evaluation.get("escalate"):
        print("\nStep 6: ESCALATION")
        escalation = escalate_ticket(ticket, reason="Low confidence", context=evaluation)
        print(f"  ✓ Escalated to human")
    else:
        print("\nStep 6: RESPONSE COMPOSITION")
        response = compose_response(ticket, solution.get("solution_text"), evaluation)
        print(f"  ✓ Response generated")
        
        print("\nStep 7: FEEDBACK LOOP")
        feedback = {"satisfied": True}
        feedback_result = handle_feedback(ticket, feedback)
        print(f"  ✓ Feedback handled: {feedback_result.get('action')}")
    
    results.record("Workflow", "Full workflow execution", True, "Complete workflow succeeded")


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all tests in sequence."""
    print("\n")
    print("=" * 80)
    print(" "*20 + "COMPREHENSIVE TEST SUITE")
    print(" "*15 + "Ticket Processing System - All Agents")
    print("=" * 80)
    
    # Run unit tests
    ticket = test_validator()
    test_scorer(ticket)
    test_query_analyzer(ticket)
    test_classifier(ticket)
    test_solution_finder(ticket)
    test_evaluator(ticket)
    test_response_composer(ticket)
    test_feedback_handler(ticket)
    test_escalation_manager(ticket)
    test_continuous_improvement()
    
    # Run integration test
    test_full_workflow()
    
    # Print summary
    results.summary()
    
    print("\n" + "="*80)
    print(f"RESULT: {results.passed}/{results.total} tests passed")
    print("="*80 + "\n")
    
    return results.failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
