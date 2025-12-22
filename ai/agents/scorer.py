# agents/scorer.py
"""Scorer Agent using Agno + Mistral LLM to compute ticket priority scores."""

from models import Ticket
from typing import Dict
import json
import os
import re
from agno.agent import Agent
from agno.models.mistral import MistralChat
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# Load API key
_mistral_key = os.environ.get("MISTRAL_API_KEY") or os.environ.get("MISTRALAI_API_KEY")
if _mistral_key:
    os.environ["MISTRALAI_API_KEY"] = _mistral_key

MODEL_ID = os.environ.get("MISTRAL_MODEL_ID", "mistral-small-latest")


def _create_scorer_agent() -> Agent:
    """Create an Agno Agent for ticket scoring."""
    mistral_model = MistralChat(id=MODEL_ID, temperature=0.3)
    
    instructions = """You are a ticket priority scoring expert. Analyze support tickets for:
1. Urgency (ASAP, immediate, production down, SLA breach)
2. Recurrence (repeating issue, known problem, chronic)
3. Impact (downtime, revenue loss, user blocked, data loss)

Return JSON with:
{
    "score": 0-100,
    "priority": "low|medium|high",
    "urgency_level": 0-1,
    "recurrence_level": 0-1,
    "impact_level": 0-1,
    "reasoning": "brief explanation"
}

Scoring logic:
- Base: 10
- Urgency >=0.7: +40
- Recurrence >=0.6: +20
- Impact >=0.7: +30
- Cap at 100"""
    
    agent = Agent(
        model=mistral_model,
        instructions=instructions,
        name="TicketScorer"
    )
    return agent


def score_ticket(ticket: Ticket) -> Dict:
    """Compute priority score (0-100) using LLM-based Agno Agent.
    
    Returns dict {"score": int, "priority": "low|medium|high"} and sets `ticket.priority_score`.
    """
    agent = _create_scorer_agent()
    
    prompt = f"""Score this support ticket for priority:
Subject: {ticket.subject}
Description: {ticket.description}

Analyze urgency, recurrence, and impact. Return JSON with score (0-100), priority (low/medium/high), and component scores."""
    
    try:
        response = agent.run(prompt)
        response_text = str(response.content) if hasattr(response, 'content') else str(response)
        
        # Extract JSON from response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
            score = max(0, min(100, result.get("score", 50)))
            ticket.priority_score = score
            return {
                "score": score,
                "priority": result.get("priority", "medium"),
                "reasoning": result.get("reasoning", "")
            }
    except Exception as e:
        # Fallback to heuristic scoring on error
        print(f"Scorer LLM error: {e}")
    
    # Fallback heuristic scorer
    URGENCY_KEYWORDS = ["urgent", "asap", "immédiat", "immédiatement", "production", "panne"]
    RECURRENCE_KEYWORDS = ["recurrent", "répét", "encore", "toujours", "de nouveau"]
    IMPACT_KEYWORDS = ["production", "downtime", "panne", "sla", "bloquant", "data"]
    
    text = (ticket.description or "").lower()
    score = 10
    
    for kw in URGENCY_KEYWORDS:
        if kw in text:
            score += 40
            break
    for kw in RECURRENCE_KEYWORDS:
        if kw in text:
            score += 20
            break
    for kw in IMPACT_KEYWORDS:
        if kw in text:
            score += 30
            break
    
    score = max(0, min(100, score))
    ticket.priority_score = score
    
    if score >= 70:
        priority = "high"
    elif score >= 35:
        priority = "medium"
    else:
        priority = "low"
    
    return {"score": score, "priority": priority, "reasoning": "fallback heuristic"}
