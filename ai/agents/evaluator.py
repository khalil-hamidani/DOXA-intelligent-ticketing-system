# agents/evaluator.py
from models import Ticket
from typing import Dict, List
import re

NEGATIVE_WORDS = [
    "insatisfait",
    "mécontent",
    "furieux",
    "en colère",
    "pas satisfait",
    "impossible",
]


def _contains_sensitive(text: str) -> bool:
    # basic PII detectors: email, phone, cc-like digits
    if not text:
        return False
    if re.search(r"\b[\w.-]+@[\w.-]+\.[a-z]{2,}\b", text):
        return True
    if re.search(r"\b\d{10,}\b", text):
        return True
    if re.search(r"\b(?:4[0-9]{12}(?:[0-9]{3})?)\b", text):
        return True
    return False


def evaluate(ticket: Ticket) -> Dict:
    """Evaluate the proposed solution and compute confidence and escalation decision.

    Returns dict: {"confidence": float, "escalate": bool, "reasons": [...], "sensitive": bool, "escalation_context": str}
    """
    reasons: List[str] = []
    priority = ticket.priority_score or 50  # Default to medium priority

    # base confidence - start high and reduce only for specific issues
    # We want to ANSWER tickets, not escalate them!
    base_conf = 0.75  # Start with good confidence

    # boost if snippets exist
    snippet_bonus = 0.0
    if ticket.snippets:
        snippet_bonus = 0.15

    # boost for having a category
    if ticket.category:
        snippet_bonus += 0.05

    confidence = base_conf + snippet_bonus
    confidence = min(1.0, confidence)

    # detect negative sentiment
    text = (ticket.description or "").lower()
    negative = any(w in text for w in NEGATIVE_WORDS)
    if negative:
        reasons.append("Ton négatif détecté")
        confidence -= 0.15

    # detect sensitive data
    sensitive = _contains_sensitive(ticket.description)
    if sensitive:
        reasons.append("Données sensibles détectées")

    # final clamp
    confidence = max(0.0, min(1.0, confidence))

    # escalation rules - only escalate when really necessary
    escalate = False
    escalation_context = None
    if confidence < 0.3:  # Very low threshold - we want to try answering!
        escalate = True
        reasons.append("Confiance insuffisante (<30%)")

    # Don't auto-escalate just for sensitive data - we can still help
    if sensitive and confidence < 0.5:
        escalate = True
        reasons.append("Données sensibles avec confiance faible")

    # prepare escalation context
    if escalate:
        escalation_context = f"Ticket {ticket.id} - categorie={ticket.category} - score={priority} - snippets={ticket.snippets} - raisons={reasons}"

    ticket.confidence = confidence
    ticket.sensitive = sensitive
    ticket.escalation_context = escalation_context

    return {
        "confidence": confidence,
        "escalate": escalate,
        "reasons": reasons,
        "sensitive": sensitive,
        "escalation_context": escalation_context,
    }
