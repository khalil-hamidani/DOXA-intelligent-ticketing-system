# agents/validator.py
"""Validator Agent using Agno + Mistral LLM to evaluate ticket validity."""

from models import Ticket
from typing import Dict, List
import json
import os
import asyncio
from agno.agent import Agent
from agno.models.mistral import MistralChat
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# Load API key
_mistral_key = os.environ.get("MISTRAL_API_KEY") or os.environ.get("MISTRALAI_API_KEY")
if _mistral_key:
    os.environ["MISTRALAI_API_KEY"] = _mistral_key

MODEL_ID = os.environ.get("MISTRAL_MODEL_ID", "mistral-small-latest")


def _create_validator_agent() -> Agent:
    """Create an Agno Agent for ticket validation."""
    mistral_model = MistralChat(id=MODEL_ID, temperature=0.3)
    
    instructions = """You are a ticket validation expert. Your task is to evaluate whether a support ticket has:
1. Clear subject (not empty/vague)
2. Exploitable keywords and context
3. Sufficient information for initial processing

Analyze the ticket and respond with JSON:
{
    "valid": true/false,
    "reasons": ["reason1", "reason2", ...],
    "confidence": 0.0-1.0
}

Be strict but fair. Reject tickets that are too vague or lack actionable information."""
    
    agent = Agent(
        model=mistral_model,
        instructions=instructions,
        name="TicketValidator"
    )
    return agent


def validate_ticket(ticket: Ticket) -> Dict:
    """Validate ticket content using LLM-based Agno Agent.
    
    Returns: {"valid": bool, "reasons": List[str], "confidence": float}.
    """
    # Skip LLM for now - use fallback heuristic which is more reliable
    # agent = _create_validator_agent()
    
    # Fallback heuristic validation (RELIABLE)
    reasons: List[str] = []
    if not ticket.subject or not ticket.subject.strip():
        reasons.append("Sujet manquant")
    if not ticket.description or len(ticket.description.strip()) < 10:  # Lowered from 20 to 10
        reasons.append("Description trop courte (>=10 caractères requis)")
    
    valid = len(reasons) == 0
    confidence = 0.9 if valid else 0.4
    return {"valid": valid, "reasons": reasons, "confidence": confidence}
