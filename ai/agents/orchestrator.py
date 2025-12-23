# agents/orchestrator.py
from agents.validator import validate_ticket
from agents.scorer import score_ticket
from agents.query_analyzer import analyze_and_reformulate, classify_ticket
from agents.solution_finder import find_solution
from agents.evaluator import evaluate
from agents.response_composer import compose_response
from agents.feedback_loop import analyze_escalations

from models import Ticket
from typing import Dict

MAX_ATTEMPTS = 2


def process_ticket(ticket: Ticket, team: str = None) -> Dict:
    """Run the full pipeline for a ticket and return structured result.

    Returns dict {"status": str, "message": str, "ticket": Ticket}
    """
    # Step 0 - validation
    v = validate_ticket(ticket)
    if not v.get("valid"):
        ticket.status = "rejected"
        return {
            "status": "invalid",
            "message": "Ticket invalide, merci de compléter le formulaire.",
            "reasons": v.get("reasons", []),
            "ticket": ticket,
        }

    # Step 1 - scoring
    score_res = score_ticket(ticket)

    # Query analysis (Agent A + B)
    analyze_res = analyze_and_reformulate(ticket)
    classify_res = classify_ticket(ticket)

    # Solution finding (RAG-like)
    sol_res = find_solution(ticket, team=team)
    solution_text = sol_res.get("solution_text")

    # Evaluation & decision
    eval_res = evaluate(ticket)
    if eval_res.get("escalate"):
        ticket.status = "escalated"
        ticket.attempts += 1
        # feedback loop trigger (store minimal data)
        analyze_escalations(ticket)
        return {
            "status": "escalated",
            "message": "Ticket escaladé vers un agent humain.",
            "escalation_context": eval_res.get("escalation_context"),
            "ticket": ticket,
        }

    # Compose response for client
    response = compose_response(ticket, solution_text, eval_res)
    ticket.status = "answered"
    ticket.response = response  # Store response in ticket for polling
    ticket.solution_text = solution_text  # Store solution text too

    return {"status": "answered", "message": response, "ticket": ticket}
