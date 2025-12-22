"""
Example: Using the Refactored Agno Agents
Complete walkthrough of the intelligent ticketing pipeline
"""

from models import Ticket
from agents.validator import validate_ticket
from agents.scorer import score_ticket
from agents.query_analyzer import analyze_and_reformulate, classify_ticket
from agents.classifier import classify_ticket_model
from agents.orchestrator import process_ticket


# ============================================================================
# Example 1: Simple Validation
# ============================================================================

def example_1_simple_validation():
    """Example 1: Validate a ticket using the Validator Agent"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Simple Validation")
    print("="*70)
    
    # Create a ticket
    ticket = Ticket(
        id="ticket_001",
        client_name="John Doe",
        email="john@example.com",
        subject="Cannot log into account",
        description="I've been trying to log in for the past hour but keep getting an 'Invalid credentials' error. I tried resetting my password but still no luck. This is urgent!"
    )
    
    print(f"\nTicket Subject: {ticket.subject}")
    print(f"Description: {ticket.description[:100]}...")
    
    # Validate
    result = validate_ticket(ticket)
    print(f"\n✓ Validation Result:")
    print(f"  - Valid: {result['valid']}")
    print(f"  - Confidence: {result.get('confidence', 0.5):.1%}")
    if not result['valid']:
        print(f"  - Reasons: {', '.join(result['reasons'])}")
    else:
        print(f"  - Status: TICKET VALID - Proceeding to processing")
    
    return ticket, result


# ============================================================================
# Example 2: Full Pipeline Processing
# ============================================================================

def example_2_full_pipeline():
    """Example 2: Process a ticket through the complete pipeline"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Full Pipeline Processing")
    print("="*70)
    
    # Create a more complex ticket
    ticket = Ticket(
        id="ticket_002",
        client_name="Acme Corp Support",
        email="support@acme.com",
        subject="Production database down - URGENT",
        description="""
        Our production database server (prod-db-01) has crashed and is no longer responding.
        All customers are currently unable to access our service.
        This happened at 2:45 PM and is still ongoing (40 minutes of downtime).
        Revenue impact is estimated at $500/minute.
        We need immediate assistance with database recovery.
        Error logs: connection refused on port 5432
        """
    )
    
    print(f"\nProcessing Ticket: {ticket.subject}")
    print(f"Client: {ticket.client_name}")
    
    # Use full orchestrator pipeline
    result = process_ticket(ticket, team="emergency_response")
    
    print(f"\n✓ Pipeline Result:")
    print(f"  - Status: {result['status']}")
    print(f"  - Message: {result['message'][:200]}...")
    
    if result['status'] == 'escalated':
        print(f"  - Escalation Context: {result.get('escalation_context', 'N/A')}")
    
    print(f"\n✓ Ticket Enriched Data:")
    print(f"  - Priority Score: {ticket.priority_score}")
    print(f"  - Category: {ticket.category}")
    print(f"  - Summary: {ticket.summary}")
    
    return ticket, result


# ============================================================================
# Example 3: Step-by-Step Agent Usage
# ============================================================================

def example_3_step_by_step():
    """Example 3: Use agents individually for fine-grained control"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Step-by-Step Agent Usage")
    print("="*70)
    
    # Create ticket
    ticket = Ticket(
        id="ticket_003",
        client_name="Jane Smith",
        email="jane@company.com",
        subject="Invoice discrepancy",
        description="""
        I received an invoice for $500.00 for May, but my subscription should only cost
        $200.00 per month. This is the second time this has happened.
        Previous invoice from April was also overcharged at $450.00.
        Can you please explain these charges and provide a refund?
        This is affecting our monthly budget reconciliation.
        """
    )
    
    print(f"\nProcessing: {ticket.subject}")
    
    # Step 1: Validate
    print("\n[Step 1] Validation")
    validation = validate_ticket(ticket)
    print(f"  Valid: {validation['valid']}")
    print(f"  Confidence: {validation.get('confidence', 0.5):.1%}")
    
    if not validation['valid']:
        print("  ✗ Ticket rejected - no further processing")
        return
    
    # Step 2: Score
    print("\n[Step 2] Scoring")
    scoring = score_ticket(ticket)
    print(f"  Score: {scoring['score']}/100")
    print(f"  Priority: {scoring['priority']}")
    print(f"  Reasoning: {scoring.get('reasoning', '')}")
    
    # Step 3: Analyze & Reformulate
    print("\n[Step 3] Analysis (Agent A: Reformulation)")
    analysis = analyze_and_reformulate(ticket)
    print(f"  Summary: {analysis['summary']}")
    print(f"  Keywords: {', '.join(analysis['keywords'][:5])}")
    
    # Step 4: Classify
    print("\n[Step 4] Classification (Agent B)")
    classification = classify_ticket(ticket)
    print(f"  Category: {classification['category']}")
    print(f"  Treatment: {classification['expected_treatment']}")
    
    # Step 5: Advanced Classification
    print("\n[Step 5] Advanced Classifier Model")
    classifier = classify_ticket_model(ticket)
    print(f"  Category: {classifier['category']}")
    print(f"  Treatment Type: {classifier['treatment_type']}")
    print(f"  Severity: {classifier['severity']}")
    print(f"  Confidence: {classifier['confidence']:.1%}")
    print(f"  Required Skills: {', '.join(classifier.get('required_skills', [])[:3])}")
    
    return ticket


# ============================================================================
# Example 4: Error Handling & Fallback
# ============================================================================

def example_4_error_handling():
    """Example 4: Demonstrate error handling and fallback behavior"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Error Handling & Fallback")
    print("="*70)
    
    # Create a minimal/problematic ticket
    ticket = Ticket(
        id="ticket_004",
        client_name="Test",
        email="test@test.com",
        subject="Help",
        description="It doesn't work"  # Vague ticket
    )
    
    print(f"\nProcessing vague ticket: {ticket.subject}")
    print(f"Description: {ticket.description}")
    
    # The validators will fail
    validation = validate_ticket(ticket)
    
    print(f"\n✓ Validation Result (with fallback):")
    print(f"  - Valid: {validation['valid']}")
    print(f"  - Reasons: {validation['reasons']}")
    print(f"  - Confidence: {validation.get('confidence', 0.5):.1%}")
    print(f"\n  Note: Even if LLM fails, heuristic fallback ensures system works")
    
    return ticket


# ============================================================================
# Example 5: Batch Processing
# ============================================================================

def example_5_batch_processing():
    """Example 5: Process multiple tickets (batch)"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Batch Processing")
    print("="*70)
    
    tickets = [
        Ticket(
            id="batch_001",
            client_name="Client A",
            email="a@example.com",
            subject="Technical issue",
            description="The API endpoint is returning 500 errors"
        ),
        Ticket(
            id="batch_002",
            client_name="Client B",
            email="b@example.com",
            subject="Billing inquiry",
            description="Why was I charged twice this month?"
        ),
        Ticket(
            id="batch_003",
            client_name="Client C",
            email="c@example.com",
            subject="Password reset",
            description="I need to reset my password"
        ),
    ]
    
    print(f"\nProcessing {len(tickets)} tickets in batch...")
    
    results = []
    for i, ticket in enumerate(tickets, 1):
        print(f"\n[{i}/{len(tickets)}] Processing: {ticket.subject}")
        result = process_ticket(ticket)
        results.append({
            'ticket_id': ticket.id,
            'status': result['status'],
            'category': ticket.category,
            'priority': ticket.priority_score
        })
        print(f"    Status: {result['status']}")
        print(f"    Category: {ticket.category}")
        print(f"    Priority: {ticket.priority_score}")
    
    # Summary
    print(f"\n✓ Batch Summary:")
    answered = sum(1 for r in results if r['status'] == 'answered')
    escalated = sum(1 for r in results if r['status'] == 'escalated')
    print(f"  - Answered: {answered}")
    print(f"  - Escalated: {escalated}")
    
    # Category breakdown
    from collections import Counter
    categories = Counter(r['category'] for r in results)
    print(f"  - By Category: {dict(categories)}")
    
    return results


# ============================================================================
# Example 6: Custom Configuration
# ============================================================================

def example_6_custom_config():
    """Example 6: Using custom configuration"""
    print("\n" + "="*70)
    print("EXAMPLE 6: Custom Configuration")
    print("="*70)
    
    from agents.config import (
        MISTRAL_API_KEY,
        MISTRAL_MODEL_ID,
        AGENT_TEMPERATURE,
        HIGH_PRIORITY_THRESHOLD,
    )
    
    print(f"\n✓ Current Configuration:")
    print(f"  - API Key: {MISTRAL_API_KEY[:10] if MISTRAL_API_KEY else 'NOT SET'}...")
    print(f"  - Model ID: {MISTRAL_MODEL_ID}")
    print(f"  - Agent Temperatures: {AGENT_TEMPERATURE}")
    print(f"  - High Priority Threshold: {HIGH_PRIORITY_THRESHOLD}")
    
    print(f"\n✓ To customize:")
    print(f"  1. Edit ai/agents/config.py")
    print(f"  2. Restart your application")
    print(f"  3. Changes apply automatically")


# ============================================================================
# Example 7: Testing & Validation
# ============================================================================

def example_7_testing():
    """Example 7: Running tests"""
    print("\n" + "="*70)
    print("EXAMPLE 7: Testing")
    print("="*70)
    
    print(f"\n✓ To run comprehensive tests:")
    print(f"  $ python ai/tests/test_agents.py")
    
    print(f"\n✓ This will run:")
    print(f"  - Validator tests (3 cases)")
    print(f"  - Scorer tests (4 cases)")
    print(f"  - Query Analyzer tests (3 cases)")
    print(f"  - Classifier tests (3 cases)")
    print(f"  - Integration tests (2 cases)")
    
    print(f"\n✓ Expected output:")
    print(f"  ✓ Validator tests completed")
    print(f"  ✓ Scorer tests completed")
    print(f"  ✓ Query Analyzer tests completed")
    print(f"  ✓ Classifier tests completed")
    print(f"  ✓ ALL AGENT TESTS COMPLETED")


# ============================================================================
# Main
# ============================================================================

def main():
    """Run all examples"""
    print("\n" + "🎯 AGNO AGENTS - COMPLETE USAGE EXAMPLES 🎯".center(70, "="))
    
    print("""
This file demonstrates 7 different ways to use the refactored Agno agents:

1. Simple Validation      - Validate a single ticket
2. Full Pipeline          - Process through complete pipeline
3. Step-by-Step           - Use individual agents
4. Error Handling         - Graceful fallback behavior
5. Batch Processing       - Process multiple tickets
6. Custom Configuration   - Customize agent behavior
7. Testing                - Run test suite

Each example is a function you can call independently.
    """)
    
    # Run examples
    try:
        # Note: These examples don't require running LLM calls
        # They demonstrate the API and structure
        
        print("\n" + "="*70)
        print("RUNNING EXAMPLES")
        print("="*70)
        
        # Example 1
        ticket1, result1 = example_1_simple_validation()
        
        # Example 2
        ticket2, result2 = example_2_full_pipeline()
        
        # Example 3
        ticket3 = example_3_step_by_step()
        
        # Example 4
        ticket4 = example_4_error_handling()
        
        # Example 5
        results5 = example_5_batch_processing()
        
        # Example 6
        example_6_custom_config()
        
        # Example 7
        example_7_testing()
        
    except Exception as e:
        print(f"\n✗ Error during examples: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)
    print("✓ EXAMPLES COMPLETED")
    print("="*70)
    
    print(f"""
Next steps:
1. Read QUICK_START.md for quick setup
2. Run: python ai/tests/test_agents.py
3. Run: python ai/demo_agents.py
4. Check documentation in root directory
5. Integrate into your application

For more info, see:
- DOCUMENTATION_INDEX.md (all guides)
- ARCHITECTURE.md (system design)
- DEPLOYMENT_GUIDE.md (production deployment)
    """)


if __name__ == "__main__":
    main()
