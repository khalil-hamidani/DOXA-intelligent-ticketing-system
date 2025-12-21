# agents/scorer.py
from models import Ticket

def score_ticket(ticket: Ticket) -> int:
    score = 0
    # Exemples simples
    if "urgent" in ticket.description.lower():
        score += 50
    if "recurrent" in ticket.description.lower():
        score += 30
    ticket.priority_score = score
    return score
