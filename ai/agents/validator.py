# agents/validator.py
from models import Ticket
from typing import Dict, List
import re

def validate_ticket(ticket: Ticket) -> Dict:
    """Validate ticket content and return structured result.

    Returns: {"valid": bool, "reasons": List[str]}.
    """
    reasons: List[str] = []

    if not ticket.subject or not ticket.subject.strip():
        reasons.append("Sujet manquant")

    if not ticket.description or len(ticket.description.strip()) < 20:
        reasons.append("Description trop courte (>=20 caractères requis)")

    # basic keyword presence (at least 2 meaningful words)
    words = [w for w in re.findall(r"\w+", ticket.description.lower()) if len(w) > 2]
    if len(words) < 3:
        reasons.append("Peu d'informations exploitables dans la description")

    valid = len(reasons) == 0
    return {"valid": valid, "reasons": reasons}
