# agents/query_analyzer.py
from models import Ticket
from typing import Dict, List
import re

def analyze_and_reformulate(ticket: Ticket) -> Dict:
    """Agent A: summarize, reformulate and extract keywords.

    Returns dict with `summary`, `reformulation`, `keywords`.
    """
    text = ticket.description.strip()
    # simple summary: first sentence or truncated
    sentences = re.split(r'[\.\n]', text)
    summary = sentences[0].strip() if sentences and sentences[0].strip() else text[:200]

    # reformulation: short rewrite (heuristic)
    reformulation = summary

    words = [w for w in re.findall(r"\w+", text.lower()) if len(w) > 3]
    keywords: List[str] = list(dict.fromkeys(words))[:8]

    ticket.summary = summary
    ticket.reformulation = reformulation
    ticket.keywords = keywords

    return {"summary": summary, "reformulation": reformulation, "keywords": keywords}


def classify_ticket(ticket: Ticket) -> Dict:
    """Agent B: classify ticket into category and expected treatment type."""
    kws = set((ticket.keywords or []) + [] )
    cat = "autre"

    if any(w in kws for w in ("facturation", "invoice", "payment", "paiement")):
        cat = "facturation"
    elif any(w in kws for w in ("error", "bug", "erreur", "panne", "crash")):
        cat = "technique"
    elif any(w in kws for w in ("accès", "login", "auth", "motdepasse")):
        cat = "authentification"

    ticket.category = cat
    return {"category": cat, "expected_treatment": "standard"}
