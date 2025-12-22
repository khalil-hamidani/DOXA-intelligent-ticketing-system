"""
Feedback Handler Agent - Step 6: Feedback Collection

Responsibilities:
  - Collect client satisfaction feedback
  - Determine action: close, retry, or escalate
  - Track attempt count
  - Manage feedback loop logic

Output:
  {"action": str, "message": str, "attempts": int, ...}
"""

from models import Ticket
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 2


def handle_feedback(ticket: Ticket, feedback: Dict) -> Dict:
    """
    Process client feedback and determine next action.
    
    Step 6: Feedback Collection
    
    Args:
        ticket: Original ticket being processed
        feedback: {"satisfied": bool, "clarification": str, ...}
    
    Returns:
        {
            "action": str ("close", "retry", "escalate"),
            "message": str,
            "attempts": int,
            "next_action": str
        }
    """
    logger.info(f"Processing feedback for ticket {ticket.id}")
    
    # Get satisfaction status
    satisfied = feedback.get("satisfied", False)
    clarification = feedback.get("clarification", "")
    
    # Track attempts
    current_attempts = getattr(ticket, 'attempts', 1)
    logger.info(f"Current attempts: {current_attempts}/{MAX_ATTEMPTS}")
    
    # ====================================================================
    # DECISION LOGIC
    # ====================================================================
    
    # Case 1: Client is satisfied
    if satisfied:
        logger.info(f"Ticket {ticket.id} - Client satisfied")
        return {
            "action": "close",
            "message": "Merci pour votre feedback! Ticket fermé.",
            "attempts": current_attempts,
            "next_action": "CLOSE"
        }
    
    # Case 2: Not satisfied - check if we can retry
    if current_attempts < MAX_ATTEMPTS:
        logger.info(f"Ticket {ticket.id} - Retrying (attempt {current_attempts + 1})")
        return {
            "action": "retry",
            "message": f"Relance du traitement avec votre clarification (tentative {current_attempts + 1}).",
            "attempts": current_attempts + 1,
            "next_action": "RETRY_FROM_STEP_2",
            "clarification": clarification
        }
    
    # Case 3: Max attempts reached - escalate
    logger.warning(f"Ticket {ticket.id} - Max attempts reached, escalating")
    return {
        "action": "escalate",
        "message": f"Après {current_attempts} tentatives, ce ticket est escaladé pour révision humaine.",
        "attempts": current_attempts,
        "next_action": "ESCALATE",
        "escalation_reason": "Max attempts exceeded - client unsatisfied"
    }


def log_feedback(ticket: Ticket, feedback: Dict) -> None:
    """
    Log feedback for analytics and continuous improvement.
    
    Step 8: Post-Analysis
    """
    logger.info(f"Feedback logged for ticket {ticket.id}")
    logger.debug(f"  Satisfied: {feedback.get('satisfied')}")
    logger.debug(f"  Clarification: {feedback.get('clarification')}")
    logger.debug(f"  Confidence: {getattr(ticket, 'confidence', 'N/A')}")
    logger.debug(f"  Category: {getattr(ticket, 'category', 'N/A')}")
