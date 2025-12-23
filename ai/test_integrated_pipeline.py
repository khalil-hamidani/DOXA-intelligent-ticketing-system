#!/usr/bin/env python3
"""
Test the unified KB-integrated orchestrator.
"""

import sys
import os

# Add paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "agents"))

from models import Ticket
from agents.orchestrator import process_ticket


def test_integrated_pipeline():
    """Test the full pipeline with KB integration."""
    
    # Create a test ticket
    ticket = Ticket(
        id="TEST_001",
        client_name="Test Client",
        email="test@example.com",
        subject="Conditions de service",
        description="Quelles sont les conditions générales de service de Doxa?",
        category="information",
        keywords=["conditions", "service", "Doxa"],
        status="pending"
    )
    
    print("=" * 70)
    print("🎫 TEST: Unified KB-Integrated Orchestrator")
    print("=" * 70)
    print(f"\n📋 Ticket: {ticket.id}")
    print(f"   Subject: {ticket.subject}")
    print(f"   Description: {ticket.description}")
    print(f"   Keywords: {ticket.keywords}")
    
    # Process ticket through full pipeline
    print("\n🔄 Processing through unified pipeline...")
    result = process_ticket(ticket, team=None)
    
    # Display results
    print(f"\n✅ Status: {result['status']}")
    print(f"\n📝 Response:\n{result['message']}")
    
    # Show KB context
    kb_ctx = result.get("kb_context", {})
    print(f"\n📚 Knowledge Base Context:")
    print(f"   Source: {kb_ctx.get('source')}")
    print(f"   Confidence: {kb_ctx.get('confidence', 0):.2%}")
    print(f"   Documents retrieved: {kb_ctx.get('num_documents', 0)}")
    
    if kb_ctx.get("documents"):
        print(f"\n   Retrieved documents:")
        for i, doc in enumerate(kb_ctx["documents"], 1):
            source = doc.get("meta", {}).get("source", "unknown")
            score = doc.get("score", 0)
            content_preview = doc.get("content", "")[:100]
            print(f"   [{i}] {source} (score: {score:.3f})")
            print(f"       {content_preview}...")
    
    print(f"\n📊 Ticket status: {ticket.status}")
    print("=" * 70)


if __name__ == "__main__":
    test_integrated_pipeline()
