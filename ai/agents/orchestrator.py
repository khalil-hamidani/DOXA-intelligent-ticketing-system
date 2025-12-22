# agents/orchestrator.py
"""
Ticket Processing Orchestrator

Implements the complete 10-step workflow:
  Step 0: Validation (Agent Validator)
  Step 1: Scoring & Prioritisation (Agent Scorer)
  Step 2: Query Analysis (Agent A + B: Analyze & Classification)
  Step 3: Solution Finding (RAG Core)
  Step 4: Evaluation & Confidence (Agent Evaluator)
  Step 5: Response Composition (Agent Composer)
  Step 6: Feedback Collection (Feedback Handler)
  Step 7: Escalation Management (Escalation Manager)
  Step 8: Post-Analysis (Continuous Improvement)
  Step 9: Metrics & Reporting

Feedback Loop: Max 2 attempts. If client unsatisfied and attempts < 2, 
restart from Step 2 with reformulated query.
"""

from agents.validator import validate_ticket
from agents.scorer import score_ticket
from agents.query_analyzer import analyze_and_reformulate
from agents.classifier import classify_ticket_model
from agents.solution_finder import find_solution
from agents.evaluator import evaluate
from agents.response_composer import compose_response
from agents.feedback_handler import handle_feedback
from agents.escalation_manager import escalate_ticket
from agents.continuous_improvment import analyze_improvements

from models import Ticket
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)
MAX_ATTEMPTS = 2
CONFIDENCE_THRESHOLD = 0.60  # 60% = escalate if lower


def process_ticket(ticket: Ticket, team: Optional[str] = None) -> Dict:
    """
    Run the full ticket processing pipeline with feedback loop support.
    
    Args:
        ticket: Ticket to process
        team: Optional team context for solution finding
    
    Returns:
        {"status": str, "message": str, "ticket": Ticket, ...}
    """
    ticket.attempts = getattr(ticket, 'attempts', 0) + 1
    
    # ========================================================================
    # STEP 0: VALIDATION
    # ========================================================================
    logger.info(f"[Attempt {ticket.attempts}] Processing ticket {ticket.id}")
    logger.info(f"Step 0: Validating ticket...")
    
    validation = validate_ticket(ticket)
    if not validation.get("valid"):
        ticket.status = "rejected"
        logger.error(f"Ticket validation failed: {validation.get('reasons')}")
        return {
            "status": "rejected",
            "message": "Ticket invalide. Merci de compléter le formulaire avec plus de détails.",
            "reasons": validation.get("reasons", []),
            "ticket": ticket
        }
    
    logger.info("✓ Ticket validation passed")
    
    # ========================================================================
    # STEP 1: SCORING & PRIORITISATION
    # ========================================================================
    logger.info("Step 1: Scoring and prioritization...")
    
    scoring = score_ticket(ticket)
    ticket.priority_score = scoring.get("score", 50)
    ticket.priority_level = scoring.get("priority", "medium")
    
    logger.info(f"✓ Priority score: {ticket.priority_score}/100 ({ticket.priority_level})")
    
    # ========================================================================
    # STEP 2: QUERY ANALYSIS (Agent A + Agent B)
    # ========================================================================
    logger.info("Step 2: Analyzing query and classifying...")
    
    # Agent A: Reformulate & Extract Keywords
    analysis = analyze_and_reformulate(ticket)
    ticket.summary = analysis.get("summary")
    ticket.reformulation = analysis.get("reformulation")
    ticket.keywords = analysis.get("keywords", [])
    ticket.entities = analysis.get("entities", [])
    
    logger.info(f"✓ Analysis: {len(ticket.keywords)} keywords identified")
    
    # Agent B: Classify ticket
    classification = classify_ticket_model(ticket)
    ticket.category = classification.get("category", "autre")
    ticket.treatment_type = classification.get("treatment_type", "standard")
    ticket.severity = classification.get("severity", "normal")
    
    logger.info(f"✓ Classification: {ticket.category} ({ticket.treatment_type})")
    
    # ========================================================================
    # STEP 3: SOLUTION FINDING (RAG Pipeline)
    # ========================================================================
    logger.info("Step 3: Finding solution from knowledge base...")
    
    solution = find_solution(ticket, team=team)
    ticket.solution_text = solution.get("solution_text")
    ticket.snippets = solution.get("snippets", [])
    ticket.solution_confidence = solution.get("confidence", 0.0)
    
    logger.info(f"✓ Found solution with {len(ticket.snippets)} supporting docs")
    
    # ========================================================================
    # STEP 4: EVALUATION & CONFIDENCE
    # ========================================================================
    logger.info("Step 4: Evaluating response quality...")
    
    evaluation = evaluate(ticket)
    ticket.confidence = evaluation.get("confidence", 0.0)
    
    # Check escalation triggers:
    # 1. Low confidence (<60%)
    # 2. Sensitive data detected
    # 3. Negative sentiment
    should_escalate = (
        ticket.confidence < CONFIDENCE_THRESHOLD or
        evaluation.get("sensitive", False) or
        evaluation.get("negative_sentiment", False)
    )
    
    logger.info(f"✓ Confidence: {ticket.confidence:.2%}")
    logger.info(f"  Escalate: {should_escalate}")
    
    # ========================================================================
    # ESCALATION DECISION
    # ========================================================================
    if should_escalate:
        logger.warning(f"Ticket {ticket.id} escalated (confidence={ticket.confidence:.2%})")
        ticket.status = "escalated"
        
        # Step 7: Escalation Management
        escalation = escalate_ticket(ticket, reason=evaluation.get("escalation_reason"), context=evaluation)
        
        return {
            "status": "escalated",
            "message": "Ce ticket a été escaladé vers un agent humain pour assistance personnalisée.",
            "escalation_id": escalation.get("escalation_id"),
            "escalation_context": evaluation,
            "ticket": ticket
        }
    
    # ========================================================================
    # STEP 5: RESPONSE COMPOSITION
    # ========================================================================
    logger.info("Step 5: Composing response...")
    
    response = compose_response(ticket, ticket.solution_text, evaluation)
    ticket.response = response
    ticket.status = "answered"
    
    logger.info(f"✓ Response generated ({len(response)} chars)")
    
    # ========================================================================
    # STEP 6: FEEDBACK LOOP
    # ========================================================================
    # Note: Feedback collection happens asynchronously from client
    # This handles the case where feedback is received and ticket needs retry
    
    return {
        "status": "answered",
        "message": response,
        "confidence": ticket.confidence,
        "ticket": ticket
    }


def process_feedback(ticket: Ticket, feedback: Dict) -> Dict:
    """
    Process client feedback and handle retry/escalation.
    
    Step 6: Feedback Collection
    Step 8: Post-Analysis
    Step 9: Continuous Improvement
    Step 10: Metrics & Reporting
    
    Args:
        ticket: Original ticket
        feedback: {"satisfied": bool, "clarification": str, ...}
    
    Returns:
        {"action": str, "ticket": Ticket, ...}
    """
    logger.info(f"Processing feedback for ticket {ticket.id}")
    
    # Step 6: Feedback Handler
    feedback_result = handle_feedback(ticket, feedback)
    action = feedback_result.get("action")
    
    # If client is satisfied, we're done
    if action in ["close", "closed"]:
        ticket.status = "closed"
        logger.info(f"Ticket {ticket.id} closed - client satisfied")
        return {
            "action": "closed",
            "message": "Merci pour votre feedback! Ticket fermé.",
            "ticket": ticket
        }
    
    # If max attempts reached, escalate
    if action in ["escalate", "escalation"]:
        ticket.status = "escalated"
        escalation = escalate_ticket(
            ticket,
            reason="Max attempts reached - client unsatisfied",
            context={"feedback": feedback, "attempts": ticket.attempts}
        )
        logger.info(f"Ticket {ticket.id} escalated after {ticket.attempts} attempts")
        return {
            "action": "escalated",
            "message": "Ce ticket a été escaladé pour une révision complète.",
            "escalation_id": escalation.get("escalation_id"),
            "ticket": ticket
        }
    
    # If retry is needed and attempts left, reprocess
    if action in ["retry", "relance"] and ticket.attempts < MAX_ATTEMPTS:
        ticket.attempts += 1
        logger.info(f"Retrying ticket {ticket.id} (attempt {ticket.attempts})")
        
        # Restart from Step 2 with reformulated query
        logger.info("Step 2 (retry): Re-analyzing with clarification...")
        
        # Update ticket with feedback clarification
        if feedback.get("clarification"):
            ticket.description = ticket.description + "\n[Clarification] " + feedback.get("clarification")
        
        # Reprocess from Step 2
        return process_ticket(ticket, team=None)
    
    # Shouldn't reach here
    logger.warning(f"Unknown feedback action: {action}")
    return {
        "action": "unknown",
        "message": "Unable to process feedback",
        "ticket": ticket
    }


def get_ticket_status(ticket: Ticket) -> Dict:
    """Get current status and metrics for a ticket."""
    return {
        "id": ticket.id,
        "status": ticket.status,
        "attempts": ticket.attempts,
        "priority_score": ticket.priority_score,
        "category": ticket.category,
        "confidence": ticket.confidence,
        "created_at": ticket.created_at if hasattr(ticket, 'created_at') else None,
        "updated_at": ticket.updated_at if hasattr(ticket, 'updated_at') else None
    }
