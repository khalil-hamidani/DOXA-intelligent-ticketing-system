# agents/scorer.py
from models import Ticket
from typing import Dict

URGENCY_KEYWORDS = ["urgent", "asap", "immédiat", "immédiatement", "tout de suite"]
RECURRENCE_KEYWORDS = ["recurrent", "répét", "encore", "toujours", "de nouveau"]
IMPACT_KEYWORDS = ["production", "downtime", "panne", "sla", "bloquant"]

def score_ticket(ticket: Ticket) -> Dict:
    """Compute a priority score (0-100) based on heuristics.

    Returns dict {"score": int, "priority": "low|medium|high"} and sets `ticket.priority_score`.
    """
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

    # clamp
    score = max(0, min(100, score))
    ticket.priority_score = score

    if score >= 70:
        priority = "high"
    elif score >= 35:
        priority = "medium"
    else:
        priority = "low"

    return {"score": score, "priority": priority}
