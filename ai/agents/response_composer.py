# agents/response_composer.py
from models import Ticket
from typing import Dict


def compose_response(ticket: Ticket, solution: str, evaluation: Dict) -> str:
    """Compose a structured response to the client.

    Includes: thanks, reformulation, proposed solution, next steps.
    """
    steps = ""
    if ticket.category == "technique":
        steps = "1) Vérifiez la configuration locale. 2) Redémarrez le service. 3) Envoyez-nous les logs si le problème persiste."
    elif ticket.category == "facturation":
        steps = "1) Vérifiez votre facture dans l'espace client. 2) Contactez le service financier si besoin."
    else:
        steps = "Merci de suivre les instructions ci-dessus et de nous confirmer si le problème est résolu."

    confidence_pct = int((ticket.confidence or 0) * 100)

    response = (
        f"Bonjour {ticket.client_name},\n\n"
        f"Merci pour votre demande : \"{ticket.subject}\"\n\n"
        f"Reformulation : {ticket.reformulation or ticket.summary or ticket.description}\n\n"
        f"Solution proposée : {solution}\n\n"
        f"Étapes recommandées : {steps}\n\n"
        f"Confiance de la solution : {confidence_pct}%\n\n"
        "Si vous êtes satisfait, indiquez-le simplement. Si non, répondez avec plus de détails et nous relancerons le traitement."
    )

    return response
