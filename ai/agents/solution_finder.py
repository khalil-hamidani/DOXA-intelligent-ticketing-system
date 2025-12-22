# agents/solution_finder.py
from models import Ticket
from typing import Dict, List, Tuple
import re

# Simple in-memory KB: each entry is (id, category, text)
KB_ENTRIES: List[Tuple[str, str, str]] = [
    ("kb_fact_1", "facturation", "Pour les questions de facturation, contactez le service financier ou consultez la FAQ facturation."),
    ("kb_tech_1", "technique", "Pour les bugs connus, vérifiez la configuration et redémarrez le service. Si le problème persiste, fournissez les logs."),
    ("kb_auth_1", "authentification", "Pour les problèmes d'accès, réinitialisez votre mot de passe depuis la page de connexion."),
    ("kb_general_1", "autre", "Merci de préciser votre demande pour que nous puissions vous aider efficacement.")
]


def _score_entry(entry_text: str, keywords: List[str]) -> int:
    text = entry_text.lower()
    score = 0
    for kw in keywords:
        if kw.lower() in text:
            score += 10
    return score


def find_solution(ticket: Ticket, top_n: int = 3, team: str = None) -> Dict:
    """Retrieve top-N KB entries and snippets based on ticket keywords and category.

    Returns dict {"results": [ {id, category, text, score}], "solution_text": str, "confidence": float }
    Also sets `ticket.snippets` with short contextual snippets.
    """
    keywords = ticket.keywords or []
    candidates = []
    for eid, cat, text in KB_ENTRIES:
        # team boosting: if a team is provided and appears in the entry id, boost it
        team_boost = 0
        if team and team.lower() in eid.lower():
            team_boost = 20

        if ticket.category and cat != ticket.category:
            # still consider but penalize
            base = 0
        else:
            base = 5
        s = base + _score_entry(text, keywords) + team_boost
        candidates.append({"id": eid, "category": cat, "text": text, "score": s})

    candidates.sort(key=lambda x: x["score"], reverse=True)
    results = candidates[:top_n]

    # extract simple snippets (first 120 chars)
    snippets = [r["text"][0:200] for r in results]
    ticket.snippets = snippets

    # aggregation: pick top text as solution
    solution_text = results[0]["text"] if results else "Aucune solution trouvée dans la KB."
    
    # calculate confidence based on top score (normalized 0-1)
    max_possible_score = 5 + (len(keywords) * 10) + 20  # base + keywords + team boost
    top_score = results[0]["score"] if results else 0
    confidence = min(1.0, max(0.0, top_score / max_possible_score)) if max_possible_score > 0 else 0.0

    return {"results": results, "solution_text": solution_text, "confidence": confidence}