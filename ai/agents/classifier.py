# agents/classifier.py
"""Classification Model using Agno Agent for ticket categorization."""

from models import Ticket
from typing import Dict
import json
import os
from agno.agent import Agent
from agno.models.mistral import MistralChat
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# Load API key
_mistral_key = os.environ.get("MISTRAL_API_KEY") or os.environ.get("MISTRALAI_API_KEY")
if _mistral_key:
    os.environ["MISTRALAI_API_KEY"] = _mistral_key

MODEL_ID = os.environ.get("MISTRAL_MODEL_ID", "mistral-small-latest")


def _create_classifier_agent() -> Agent:
    """Create an Agno Agent for ticket classification."""
    mistral_model = MistralChat(id=MODEL_ID, temperature=0.3)
    
    instructions = """You are a support ticket classifier. Your task is to categorize tickets into:

CATEGORIES:
- technique: Technical issues (bugs, errors, crashes, system problems)
- facturation: Billing/payment issues (invoices, pricing, charges, subscriptions)
- authentification: Access/login issues (password reset, account access, permissions)
- autre: Anything else not fitting above categories but limit to max 10 categories.

TREATMENT TYPES:
- standard: Normal processing, no urgency
- priority: Needs faster handling
- escalation: Needs specialist/manager review
- urgent: Immediate action required

Return JSON:
{
    "category": "technique|facturation|authentification|autre",
    "treatment_type": "standard|priority|escalation|urgent",
    "severity": "low|medium|high",
    "reasoning": "explanation for classification",
    "confidence": 0.0-1.0,
    "required_skills": ["skill1", "skill2", ...]
}"""
    
    agent = Agent(
        model=mistral_model,
        instructions=instructions,
        name="TicketClassifier"
    )
    return agent


def classify_ticket_model(ticket: Ticket) -> Dict:
    """Classify ticket using LLM-based Agno Agent.
    
    Args:
        ticket: Ticket object
    
    Returns:
        Dict with: category, treatment_type, severity, reasoning, confidence, required_skills
    """
    agent = _create_classifier_agent()
    
    prompt = f"""Classify this support ticket:
Subject: {ticket.subject}
Description: {ticket.description}
Priority Score: {ticket.priority_score or 'N/A'}
Keywords: {', '.join(ticket.keywords or [])}
Client: {ticket.client_name}

Provide classification details in JSON format."""
    
    try:
        response = agent.run(prompt)
        response_text = str(response.content) if hasattr(response, 'content') else str(response)
        
        # Extract JSON from response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
            
            # Update ticket
            ticket.category = result.get("category", "autre")
            
            return {
                "category": result.get("category", "autre"),
                "treatment_type": result.get("treatment_type", "standard"),
                "severity": result.get("severity", "medium"),
                "reasoning": result.get("reasoning", ""),
                "confidence": result.get("confidence", 0.7),
                "required_skills": result.get("required_skills", [])
            }
    except Exception as e:
        print(f"Classifier LLM error: {e}")
    
    # Fallback heuristic classification
    keywords = set(ticket.keywords or [])
    text = (ticket.description or "").lower()
    
    category = "autre"
    if any(w in keywords or w in text for w in ("facturation", "invoice", "payment", "paiement", "billing", "prix")):
        category = "facturation"
    elif any(w in keywords or w in text for w in ("error", "bug", "erreur", "panne", "crash", "technique", "système")):
        category = "technique"
    elif any(w in keywords or w in text for w in ("accès", "login", "auth", "motdepasse", "password", "authentification")):
        category = "authentification"
    
    ticket.category = category
    
    # Determine treatment type based on priority
    treatment_type = "standard"
    if ticket.priority_score and ticket.priority_score >= 70:
        treatment_type = "urgent"
    elif ticket.priority_score and ticket.priority_score >= 50:
        treatment_type = "priority"
    
    severity = "high" if ticket.priority_score and ticket.priority_score >= 70 else \
               "medium" if ticket.priority_score and ticket.priority_score >= 35 else "low"
    
    return {
        "category": category,
        "treatment_type": treatment_type,
        "severity": severity,
        "reasoning": "fallback heuristic classification",
        "confidence": 0.6,
        "required_skills": []
    }
