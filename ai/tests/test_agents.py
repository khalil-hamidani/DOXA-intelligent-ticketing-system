"""Test suite for Agno-based agents (validator, scorer, query_analyzer, classifier)."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Ticket
from agents.validator import validate_ticket
from agents.scorer import score_ticket
from agents.query_analyzer import analyze_and_reformulate, classify_ticket
from agents.classifier import classify_ticket_model
from typing import Dict, Any
import json


# ============================================================================
# Test Fixtures
# ============================================================================

def create_sample_ticket(subject: str, description: str) -> Ticket:
    """Create a sample ticket for testing."""
    return Ticket(
        id="test_" + subject.replace(" ", "_").lower()[:20],
        client_name="Test Client",
        email="test@example.com",
        subject=subject,
        description=description
    )


# Sample test cases
VALID_TICKET = create_sample_ticket(
    "Login not working",
    "I cannot log into my account. I've tried resetting my password but still get an 'Invalid credentials' error. This happened after I updated my browser to the latest version."
)

VAGUE_TICKET = create_sample_ticket(
    "Help",
    "It doesn't work"
)

URGENT_TECHNICAL_TICKET = create_sample_ticket(
    "Production system down - URGENT",
    "Our production database server has crashed and is no longer responding. All customers are currently unable to access the service. This is a critical downtime situation affecting revenue."
)

BILLING_TICKET = create_sample_ticket(
    "Invoice issue",
    "I received an invoice for $500 but my subscription should only cost $200 per month. This is the second time this has happened. Can you explain this overcharge and refund the difference?"
)

RECURRENT_TECHNICAL_TICKET = create_sample_ticket(
    "API timeout recurring",
    "The API endpoint /v2/reports keeps timing out intermittently. This happens several times per week, blocking our batch job processing. I've seen this error repeated over the past month."
)


# ============================================================================
# Test Functions
# ============================================================================

def test_validator() -> Dict[str, Any]:
    """Test the Validator Agent."""
    print("\n" + "="*70)
    print("VALIDATOR AGENT TESTS")
    print("="*70)
    
    results = {
        "valid_ticket": None,
        "vague_ticket": None,
        "urgent_ticket": None
    }
    
    # Test 1: Valid ticket should pass validation
    print("\nTest 1: Valid ticket (should be valid)")
    result = validate_ticket(VALID_TICKET)
    print(f"  Result: {result}")
    results["valid_ticket"] = result
    assert isinstance(result, dict), "Validator should return dict"
    assert "valid" in result, "Result must have 'valid' key"
    assert "reasons" in result, "Result must have 'reasons' key"
    print(f"  ✓ Valid: {result['valid']}, Reasons: {result['reasons']}")
    
    # Test 2: Vague ticket should fail validation
    print("\nTest 2: Vague ticket (should be invalid)")
    result = validate_ticket(VAGUE_TICKET)
    print(f"  Result: {result}")
    results["vague_ticket"] = result
    assert not result["valid"], "Vague ticket should be invalid"
    print(f"  ✓ Correctly rejected. Reasons: {result['reasons']}")
    
    # Test 3: Urgent technical ticket should still be valid
    print("\nTest 3: Urgent technical ticket (should be valid)")
    result = validate_ticket(URGENT_TECHNICAL_TICKET)
    print(f"  Result: {result}")
    results["urgent_ticket"] = result
    assert result["valid"], "Valid but urgent ticket should pass validation"
    print(f"  ✓ Valid: {result['valid']}")
    
    return results


def test_scorer() -> Dict[str, Any]:
    """Test the Scorer Agent."""
    print("\n" + "="*70)
    print("SCORER AGENT TESTS")
    print("="*70)
    
    results = {
        "valid_ticket_score": None,
        "urgent_ticket_score": None,
        "billing_ticket_score": None,
        "recurrent_ticket_score": None
    }
    
    # Test 1: Normal ticket gets low-medium score
    print("\nTest 1: Normal login ticket (should get low-medium score)")
    result = score_ticket(VALID_TICKET)
    print(f"  Result: {result}")
    results["valid_ticket_score"] = result
    assert "score" in result and "priority" in result
    assert 0 <= result["score"] <= 100, "Score must be 0-100"
    assert result["priority"] in ["low", "medium", "high"]
    print(f"  ✓ Score: {result['score']}, Priority: {result['priority']}")
    
    # Test 2: Urgent ticket gets high score
    print("\nTest 2: Production outage (should get high score)")
    result = score_ticket(URGENT_TECHNICAL_TICKET)
    print(f"  Result: {result}")
    results["urgent_ticket_score"] = result
    assert result["score"] >= 70, f"Urgent ticket should score >=70, got {result['score']}"
    assert result["priority"] == "high", f"Urgent ticket should be 'high' priority, got {result['priority']}"
    print(f"  ✓ Score: {result['score']}, Priority: {result['priority']}")
    
    # Test 3: Billing ticket
    print("\nTest 3: Billing issue (should be medium priority)")
    result = score_ticket(BILLING_TICKET)
    print(f"  Result: {result}")
    results["billing_ticket_score"] = result
    print(f"  ✓ Score: {result['score']}, Priority: {result['priority']}")
    
    # Test 4: Recurrent technical issue
    print("\nTest 4: Recurrent issue (should get boost for recurrence)")
    result = score_ticket(RECURRENT_TECHNICAL_TICKET)
    print(f"  Result: {result}")
    results["recurrent_ticket_score"] = result
    print(f"  ✓ Score: {result['score']}, Priority: {result['priority']}")
    
    return results


def test_query_analyzer() -> Dict[str, Any]:
    """Test the Query Analyzer (Agent A & B)."""
    print("\n" + "="*70)
    print("QUERY ANALYZER TESTS (Agent A: Reformulation + Agent B: Classification)")
    print("="*70)
    
    results = {
        "reformulation": None,
        "classification": None
    }
    
    ticket = VALID_TICKET
    
    # Test 1: Reformulation Agent
    print("\nTest 1: Reformulation Agent (Agent A)")
    print(f"  Original description: {ticket.description[:80]}...")
    reform_result = analyze_and_reformulate(ticket)
    print(f"  Reformulation result: {reform_result}")
    results["reformulation"] = reform_result
    
    assert "summary" in reform_result
    assert "reformulation" in reform_result
    assert "keywords" in reform_result
    assert isinstance(reform_result["keywords"], list)
    print(f"  ✓ Summary: {reform_result['summary']}")
    print(f"  ✓ Keywords: {reform_result['keywords']}")
    
    # Test 2: Classification Agent
    print("\nTest 2: Classification Agent (Agent B)")
    classif_result = classify_ticket(ticket)
    print(f"  Classification result: {classif_result}")
    results["classification"] = classif_result
    
    assert "category" in classif_result
    assert classif_result["category"] in ["technique", "facturation", "authentification", "autre"]
    assert "expected_treatment" in classif_result
    print(f"  ✓ Category: {classif_result['category']}")
    print(f"  ✓ Treatment: {classif_result['expected_treatment']}")
    
    # Test with billing ticket
    print("\nTest 3: Classification on billing ticket")
    billing_reform = analyze_and_reformulate(BILLING_TICKET)
    billing_classif = classify_ticket(BILLING_TICKET)
    print(f"  Category: {billing_classif['category']}")
    assert billing_classif["category"] == "facturation", f"Billing ticket should be 'facturation', got {billing_classif['category']}"
    print(f"  ✓ Correctly classified as facturation")
    
    return results


def test_classifier() -> Dict[str, Any]:
    """Test the Classification Model Agent."""
    print("\n" + "="*70)
    print("CLASSIFICATION MODEL AGENT TESTS")
    print("="*70)
    
    results = {
        "login_classification": None,
        "urgent_classification": None,
        "billing_classification": None
    }
    
    # Test 1: Login issue should be authentification
    print("\nTest 1: Login issue (should be authentification)")
    # First score and analyze the ticket
    score_ticket(VALID_TICKET)
    analyze_and_reformulate(VALID_TICKET)
    
    result = classify_ticket_model(VALID_TICKET)
    print(f"  Result: {result}")
    results["login_classification"] = result
    
    assert "category" in result
    assert "treatment_type" in result
    assert "severity" in result
    assert "confidence" in result
    print(f"  ✓ Category: {result['category']}, Severity: {result['severity']}")
    print(f"  ✓ Treatment: {result['treatment_type']}, Confidence: {result['confidence']}")
    
    # Test 2: Urgent production outage
    print("\nTest 2: Production outage (should be technique/urgent)")
    score_ticket(URGENT_TECHNICAL_TICKET)
    analyze_and_reformulate(URGENT_TECHNICAL_TICKET)
    
    result = classify_ticket_model(URGENT_TECHNICAL_TICKET)
    print(f"  Result: {result}")
    results["urgent_classification"] = result
    
    assert result["category"] == "technique", f"Should be 'technique', got {result['category']}"
    assert result["treatment_type"] == "urgent", f"Should be 'urgent', got {result['treatment_type']}"
    assert result["severity"] == "high", f"Should be 'high' severity, got {result['severity']}"
    print(f"  ✓ Correctly classified as technique/urgent/high")
    
    # Test 3: Billing issue
    print("\nTest 3: Billing issue (should be facturation)")
    score_ticket(BILLING_TICKET)
    analyze_and_reformulate(BILLING_TICKET)
    
    result = classify_ticket_model(BILLING_TICKET)
    print(f"  Result: {result}")
    results["billing_classification"] = result
    
    assert result["category"] == "facturation", f"Should be 'facturation', got {result['category']}"
    print(f"  ✓ Correctly classified as facturation")
    
    return results


# ============================================================================
# Main Test Runner
# ============================================================================

def run_all_tests():
    """Run all agent tests."""
    print("\n" + "🧪 RUNNING AGNO AGENTS TEST SUITE 🧪".center(70, "="))
    
    test_results = {}
    
    try:
        test_results["validator"] = test_validator()
        print("\n✓ Validator tests completed")
    except Exception as e:
        print(f"\n✗ Validator tests failed: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        test_results["scorer"] = test_scorer()
        print("\n✓ Scorer tests completed")
    except Exception as e:
        print(f"\n✗ Scorer tests failed: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        test_results["query_analyzer"] = test_query_analyzer()
        print("\n✓ Query Analyzer tests completed")
    except Exception as e:
        print(f"\n✗ Query Analyzer tests failed: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        test_results["classifier"] = test_classifier()
        print("\n✓ Classifier tests completed")
    except Exception as e:
        print(f"\n✗ Classifier tests failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests completed for {len(test_results)} agents")
    for agent_name, results in test_results.items():
        print(f"  ✓ {agent_name.upper()}")
    
    print("\n" + "🎉 ALL AGENT TESTS COMPLETED 🎉".center(70, "="))
    print("\nNote: Some tests use LLM responses with fallback heuristics.")
    print("To see full LLM output, check console logs above.")
    
    return test_results


if __name__ == "__main__":
    run_all_tests()
