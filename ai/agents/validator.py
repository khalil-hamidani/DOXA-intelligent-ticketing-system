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

    instructions = """You are a helpful ticket validation assistant. Your goal is to ACCEPT tickets whenever possible so we can help customers.

A ticket is VALID if it has:
1. Any subject (even short ones are fine)
2. Any description that mentions a problem, question, or request
3. Basic context about what the customer needs

Be PERMISSIVE and HELPFUL. Only reject tickets that are:
- Completely empty or just random characters
- Obvious spam or test messages
- Completely unintelligible

Most real customer requests should be ACCEPTED, even if brief or informal.

Respond with JSON:
{
    "valid": true/false,
    "reasons": ["reason1", "reason2", ...],
    "confidence": 0.0-1.0
}

Default to valid=true unless there's a strong reason to reject."""

    agent = Agent(
        model=mistral_model, instructions=instructions, name="TicketValidator"
    )
    return agent


def validate_ticket(ticket: Ticket) -> Dict:
    """Validate ticket content using LLM-based Agno Agent.

    Returns: {"valid": bool, "reasons": List[str], "confidence": float}.
    """
    agent = _create_validator_agent()

    prompt = f"""Validate this support ticket:
Subject: {ticket.subject}
Description: {ticket.description}
Client: {ticket.client_name}

Respond with JSON containing valid (bool), reasons (list of strings), and confidence (0-1)."""

    # Run agent and parse response
    try:
        response = agent.run(prompt)
        response_text = (
            str(response.content) if hasattr(response, "content") else str(response)
        )

        # Extract JSON from response
        json_start = response_text.find("{")
        json_end = response_text.rfind("}") + 1
        if json_start != -1 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
            return {
                "valid": result.get("valid", False),
                "reasons": result.get("reasons", []),
                "confidence": result.get("confidence", 0.5),
            }
    except Exception as e:
        # Fallback to basic validation on error
        print(f"Validator LLM error: {e}")

    # Fallback heuristic validation - be permissive!
    reasons: List[str] = []
    if not ticket.subject or not ticket.subject.strip():
        reasons.append("Sujet manquant")
    if not ticket.description or len(ticket.description.strip()) < 5:
        reasons.append("Description trop courte (>=5 caractères requis)")

    valid = len(reasons) == 0
    return {"valid": valid, "reasons": reasons, "confidence": 0.85 if valid else 0.5}
