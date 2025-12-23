from models import Ticket
from typing import Dict, List


def analyze_escalations(ticket: Ticket) -> Dict:
	"""Very small feedback analyzer for escalated tickets.

	Returns suggestions for KB updates and notes about common patterns.
	"""
	suggestions: List[str] = []
	desc = (ticket.description or "").lower()

	if "mot de passe" in desc or "login" in desc or "auth" in desc:
		suggestions.append("Ajouter un article KB: résolution des problèmes d'authentification (reset password, 2FA)")

	if "facture" in desc or "paiement" in desc:
		suggestions.append("Vérifier et enrichir la FAQ facturation avec cas clients fréquents")

	if ticket.sensitive:
		suggestions.append("Marquer comme cas sensible et revoir le traitement automatique (ne pas exposer PII)")

	# fallback
	if not suggestions:
		suggestions.append("Analyser ce cas manuellement pour identifier un pattern récurrent.")

	# Here we would persist findings or enqueue an update to KB; for now return suggestions
	return {"ticket_id": ticket.id, "suggestions": suggestions}
