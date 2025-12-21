# agents/solution_finder.py
from models import Ticket

KB = {
    "facturation": "Pour les questions de facturation, contactez le service financier.",
    "technique": "Pour les bugs, vérifiez la configuration et redémarrez le service.",
    "autre": "Pour d'autres demandes, merci de préciser votre besoin."
}

def find_solution(ticket: Ticket) -> str:
    return KB.get(ticket.category, "Merci de préciser votre demande.")
