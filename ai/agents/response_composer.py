# agents/response_composer.py
from models import Ticket

def compose_response(ticket: Ticket, solution: str) -> str:
    return f"""
Bonjour {ticket.client_name},

Nous avons bien reçu votre demande : "{ticket.subject}"
Résumé de votre problème : {ticket.description}

Solution proposée : {solution}

Merci pour votre retour.
"""
