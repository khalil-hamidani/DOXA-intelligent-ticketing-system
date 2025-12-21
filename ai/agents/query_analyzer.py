# agents/query_analyzer.py
from models import Ticket

def analyze_ticket(ticket: Ticket) -> Ticket:
    # Agent A : keywords (simplifié)
    words = ticket.description.lower().split()
    ticket.keywords = list(set(words))[:5]
    
    # Agent B : classification simple
    if "payment" in words:
        ticket.category = "facturation"
    elif "error" in words or "bug" in words:
        ticket.category = "technique"
    else:
        ticket.category = "autre"
    return ticket
