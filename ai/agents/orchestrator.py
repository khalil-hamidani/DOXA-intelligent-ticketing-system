# agents/orchestrator.py
from agents.validator import validate_ticket
from agents.scorer import score_ticket
from agents.query_analyzer import analyze_ticket
from agents.solution_finder import find_solution
from agents.evaluator import evaluate
from agents.response_composer import compose_response

from models import Ticket

def process_ticket(ticket: Ticket) -> str:
    if not validate_ticket(ticket):
        return "Ticket invalide, merci de compléter le formulaire."
    
    score_ticket(ticket)
    analyze_ticket(ticket)
    solution = find_solution(ticket)
    
    if not evaluate(ticket):
        return "Ticket escaladé vers un agent humain."
    
    response = compose_response(ticket, solution)
    return response
