# agents/evaluator.py
from models import Ticket

def evaluate(ticket: Ticket) -> bool:
    # Simplicité : confiance = priorité score / 100
    confidence = ticket.priority_score / 100
    # Escalade si score < 60%
    return confidence >= 0.6
