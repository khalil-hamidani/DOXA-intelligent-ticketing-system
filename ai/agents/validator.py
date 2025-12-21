# agents/validator.py
from models import Ticket

def validate_ticket(ticket: Ticket) -> bool:
    if not ticket.description or len(ticket.description) < 20:
        return False
    if not ticket.subject:
        return False
    # Extra checks : presence de mots clés exploitables
    return True
