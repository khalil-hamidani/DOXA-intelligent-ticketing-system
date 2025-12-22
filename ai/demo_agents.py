#!/usr/bin/env python3
"""
Demo script showing the refactored Agno agents in action.
Demonstrates: Validator → Scorer → Query Analyzer → Classifier pipeline.
"""

import sys
import os

# Force UTF-8 encoding for Windows terminals
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import Ticket
from agents.validator import validate_ticket
from agents.scorer import score_ticket
from agents.query_analyzer import analyze_and_reformulate, classify_ticket
from agents.classifier import classify_ticket_model
from datetime import datetime


def create_demo_ticket(subject: str, description: str) -> Ticket:
    """Create a demo ticket."""
    return Ticket(
        id=f"demo_{datetime.now().timestamp()}",
        client_name="Demo Client",
        email="demo@example.com",
        subject=subject,
        description=description
    )


def demo_validator():
    """Demonstrate the Validator Agent."""
    print("\n" + "="*70)
    print("🔍 VALIDATOR AGENT DEMO")
    print("="*70)
    
    ticket = create_demo_ticket(
        "Login not working",
        "I cannot log into my account. I've tried resetting my password but still get an 'Invalid credentials' error. This happened after I updated my browser."
    )
    
    print(f"\nTicket Subject: {ticket.subject}")
    print(f"Ticket Description: {ticket.description}")
    print("\nValidating...")
    
    result = validate_ticket(ticket)
    print(f"✓ Validation Result: {result}")
    
    if result['valid']:
        print("✓ Ticket VALID - proceeding to scoring")
    else:
        print(f"✗ Ticket INVALID - Reasons: {result['reasons']}")
    
    return ticket, result


def demo_scorer(ticket: Ticket):
    """Demonstrate the Scorer Agent."""
    print("\n" + "="*70)
    print("📊 SCORER AGENT DEMO")
    print("="*70)
    
    print(f"\nTicket: {ticket.subject}")
    print("Analyzing priority...")
    
    result = score_ticket(ticket)
    print(f"✓ Score Result: {result}")
    print(f"  Priority Score: {result['score']}/100")
    print(f"  Priority Level: {result['priority'].upper()}")
    
    return result


def demo_query_analyzer(ticket: Ticket):
    """Demonstrate the Query Analyzer (2 agents)."""
    print("\n" + "="*70)
    print("🔤 QUERY ANALYZER DEMO (Agent A + Agent B)")
    print("="*70)
    
    print(f"\nTicket: {ticket.subject}")
    
    # Agent A: Reformulation
    print("\n[Agent A: Reformulation & Keywords]")
    reform_result = analyze_and_reformulate(ticket)
    print(f"  Summary: {reform_result['summary']}")
    print(f"  Reformulation: {reform_result['reformulation']}")
    print(f"  Keywords: {reform_result['keywords']}")
    
    # Agent B: Classification
    print("\n[Agent B: Classification]")
    classif_result = classify_ticket(ticket)
    print(f"  Category: {classif_result['category']}")
    print(f"  Expected Treatment: {classif_result['expected_treatment']}")
    
    return reform_result, classif_result


def demo_classifier(ticket: Ticket):
    """Demonstrate the Classification Model Agent."""
    print("\n" + "="*70)
    print("🏷️ CLASSIFICATION MODEL AGENT DEMO")
    print("="*70)
    
    print(f"\nTicket: {ticket.subject}")
    print("Detailed classification analysis...")
    
    result = classify_ticket_model(ticket)
    print(f"\n✓ Classification Result:")
    print(f"  Category: {result['category']}")
    print(f"  Treatment Type: {result['treatment_type']}")
    print(f"  Severity: {result['severity']}")
    print(f"  Confidence: {result['confidence']:.1%}")
    print(f"  Reasoning: {result['reasoning']}")
    
    return result


def run_full_pipeline_demo():
    """Run the full agent pipeline."""
    print("\n" + "🚀 FULL AGNO AGENTS PIPELINE DEMO 🚀".center(70, "="))
    
    # Example 1: Normal ticket
    print("\n" + "─"*70)
    print("EXAMPLE 1: Login Issue")
    print("─"*70)
    
    ticket1, val1 = demo_validator()
    if val1['valid']:
        demo_scorer(ticket1)
        demo_query_analyzer(ticket1)
        demo_classifier(ticket1)
    
    # Example 2: Production issue
    print("\n" + "─"*70)
    print("EXAMPLE 2: Production Outage (Urgent)")
    print("─"*70)
    
    ticket2 = create_demo_ticket(
        "Production database down - URGENT",
        "Our production database has crashed and is no longer responding. All customers are unable to access the service. This is a critical situation affecting revenue. Need immediate attention!"
    )
    
    ticket2_val, _ = validate_ticket(ticket2), None
    val_result = validate_ticket(ticket2)
    if val_result['valid']:
        demo_scorer(ticket2)
        demo_query_analyzer(ticket2)
        demo_classifier(ticket2)
    
    # Example 3: Billing issue
    print("\n" + "─"*70)
    print("EXAMPLE 3: Billing Issue")
    print("─"*70)
    
    ticket3 = create_demo_ticket(
        "Incorrect invoice amount",
        "I received an invoice for $500 but my subscription should only cost $200 per month. This is the second time this has happened. Can you explain this overcharge?"
    )
    
    val_result = validate_ticket(ticket3)
    if val_result['valid']:
        demo_scorer(ticket3)
        demo_query_analyzer(ticket3)
        demo_classifier(ticket3)
    
    print("\n" + "="*70)
    print("✓ DEMO COMPLETED")
    print("="*70)
    print("\nKey Features Demonstrated:")
    print("  ✓ Validator Agent (LLM-based ticket validation)")
    print("  ✓ Scorer Agent (Priority scoring with urgency/recurrence/impact)")
    print("  ✓ Query Analyzer (Agent A + B for reformulation & classification)")
    print("  ✓ Classifier Model (Detailed categorization & treatment planning)")
    print("\nAll agents use Mistral LLM with Agno framework.")
    print("Fallback heuristics available for API errors.")


if __name__ == "__main__":
    try:
        run_full_pipeline_demo()
    except Exception as e:
        print(f"\n✗ Error during demo: {e}")
        import traceback
        traceback.print_exc()
