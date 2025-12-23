# agents/query_analyzer.py
"""Query Analyzer using Agno Team with 2 agents:
- Agent A: Reformulation & keyword extraction
- Agent B: Ticket classification (category, treatment type)
"""

from models import Ticket
from typing import Dict, List
import json
import os
from agno.agent import Agent
from agno.models.mistral import MistralChat
from agno.team import Team
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# Load API key
_mistral_key = os.environ.get("MISTRAL_API_KEY") or os.environ.get("MISTRALAI_API_KEY")
if _mistral_key:
    os.environ["MISTRALAI_API_KEY"] = _mistral_key

MODEL_ID = os.environ.get("MISTRAL_MODEL_ID", "mistral-small-latest")


def _create_reformulation_agent() -> Agent:
    """Agent A: Reformulate ticket and extract keywords."""
    mistral_model = MistralChat(id=MODEL_ID, temperature=0.4)
    
    instructions = """You are a ticket analysis expert. Your task is to:
1. Summarize the main issue in one sentence
2. Reformulate the problem clearly and concisely
3. Extract 5-8 key technical/business terms

Return JSON:
{
    "summary": "one-line summary",
    "reformulation": "clear problem statement",
    "keywords": ["keyword1", "keyword2", ...],
    "entities": ["entity1", "entity2", ...]
}"""
    
    agent = Agent(
        model=mistral_model,
        instructions=instructions,
        name="ReformulationAgent"
    )
    return agent


def _create_classification_agent() -> Agent:
    """Agent B: Classify ticket type and suggest treatment."""
    mistral_model = MistralChat(id=MODEL_ID, temperature=0.3)
    
    instructions = """You are a ticket classification expert. Categorize the issue into ONE of:
- technique: Technical/system issues, errors, bugs, crashes
- facturation: Billing, invoicing, payment, subscription
- authentification: Login, access, password, auth errors
- autre: Other issues not fitting above

Also suggest treatment priority and action type.

Return JSON:
{
    "category": "technique|facturation|authentification|autre",
    "expected_treatment": "standard|urgent|escalation",
    "treatment_action": "brief action description",
    "confidence": 0.0-1.0
}"""
    
    agent = Agent(
        model=mistral_model,
        instructions=instructions,
        name="ClassificationAgent"
    )
    return agent


def analyze_and_reformulate(ticket: Ticket) -> Dict:
    """Agent A: Summarize, reformulate and extract keywords.
    
    Returns dict with `summary`, `reformulation`, `keywords`, `entities`.
    """
    agent = _create_reformulation_agent()
    
    prompt = f"""Analyze and reformulate this support ticket:
Subject: {ticket.subject}
Description: {ticket.description}

Provide summary, clear reformulation, and extract key terms."""
    
    try:
        response = agent.run(prompt)
        response_text = str(response.content) if hasattr(response, 'content') else str(response)
        
        # Extract JSON from response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
            
            ticket.summary = result.get("summary", "")
            ticket.reformulation = result.get("reformulation", "")
            ticket.keywords = result.get("keywords", [])
            
            return {
                "summary": ticket.summary,
                "reformulation": ticket.reformulation,
                "keywords": ticket.keywords,
                "entities": result.get("entities", [])
            }
    except Exception as e:
        print(f"Reformulation Agent error: {e}")
    
    # Fallback heuristic
    import re
    text = ticket.description.strip()
    sentences = re.split(r'[\.\n]', text)
    summary = sentences[0].strip() if sentences and sentences[0].strip() else text[:100]
    
    words = [w for w in re.findall(r"\w+", text.lower()) if len(w) > 3]
    keywords: List[str] = list(dict.fromkeys(words))[:8]
    
    ticket.summary = summary
    ticket.reformulation = summary
    ticket.keywords = keywords
    
    return {
        "summary": summary,
        "reformulation": summary,
        "keywords": keywords,
        "entities": []
    }


def classify_ticket(ticket: Ticket) -> Dict:
    """Agent B: Classify ticket into category and expected treatment type.
    
    Returns dict with `category` and `expected_treatment`.
    """
    agent = _create_classification_agent()
    
    prompt = f"""Classify this support ticket:
Subject: {ticket.subject}
Description: {ticket.description}
Summary: {ticket.summary or 'N/A'}
Keywords: {', '.join(ticket.keywords or [])}

Determine the category (technique/facturation/authentification/autre) and treatment approach."""
    
    try:
        response = agent.run(prompt)
        response_text = str(response.content) if hasattr(response, 'content') else str(response)
        
        # Extract JSON from response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
            
            ticket.category = result.get("category", "autre")
            
            return {
                "category": ticket.category,
                "expected_treatment": result.get("expected_treatment", "standard"),
                "treatment_action": result.get("treatment_action", "")
            }
    except Exception as e:
        print(f"Classification Agent error: {e}")
    
    # Fallback heuristic classification
    kws = set((ticket.keywords or []))
    cat = "autre"
    
    if any(w in kws for w in ("facturation", "invoice", "payment", "paiement", "billing")):
        cat = "facturation"
    elif any(w in kws for w in ("error", "bug", "erreur", "panne", "crash", "technique")):
        cat = "technique"
    elif any(w in kws for w in ("accès", "login", "auth", "motdepasse", "password", "authentification")):
        cat = "authentification"
    
    ticket.category = cat
    return {"category": cat, "expected_treatment": "standard", "treatment_action": ""}
