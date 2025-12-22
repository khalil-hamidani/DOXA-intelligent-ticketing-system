"""
Escalation Manager Agent - Step 7: Escalation Management

Responsibilities:
  - Route ticket to human agent
  - Create escalation record
  - Send notification email
  - Store escalation context

Output:
  {"escalation_id": str, "notification_sent": bool, ...}
"""

from models import Ticket
from typing import Dict, Optional
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


def escalate_ticket(ticket: Ticket, reason: Optional[str] = None, context: Optional[Dict] = None) -> Dict:
    """
    Escalate ticket to human agent for manual review.
    
    Step 7: Escalation Management
    
    Args:
        ticket: Ticket to escalate
        reason: Reason for escalation
        context: Additional context (evaluation results, etc.)
    
    Returns:
        {
            "escalation_id": str,
            "notification_sent": bool,
            "status": str,
            "message": str
        }
    """
    logger.info(f"Escalating ticket {ticket.id}")
    
    # Generate escalation ID
    escalation_id = f"ESC_{uuid.uuid4().hex[:8].upper()}"
    
    # Store escalation context
    escalation_data = {
        "escalation_id": escalation_id,
        "ticket_id": ticket.id,
        "client_name": ticket.client_name,
        "client_email": ticket.client_email if hasattr(ticket, 'client_email') else ticket.email,
        "subject": ticket.subject,
        "category": getattr(ticket, 'category', 'autre'),
        "priority_score": getattr(ticket, 'priority_score', 0),
        "confidence": getattr(ticket, 'confidence', 0.0),
        "reason": reason or "Escalation initié par le système",
        "timestamp": datetime.now().isoformat(),
        "context": context or {}
    }
    
    logger.debug(f"Escalation data: {escalation_data}")
    
    # Simulate sending notification email
    notification_sent = _send_escalation_email(escalation_data)
    
    # Mark ticket as escalated
    ticket.status = "escalated"
    ticket.escalation_id = escalation_id
    
    logger.info(f"Ticket {ticket.id} escalated with ID {escalation_id}")
    
    return {
        "escalation_id": escalation_id,
        "notification_sent": notification_sent,
        "status": "escalated",
        "message": f"Ticket escaladé à {escalation_id}",
        "escalation_data": escalation_data
    }


def _send_escalation_email(escalation_data: Dict) -> bool:
    """
    Send escalation notification email to support team.
    
    In production, this would connect to actual email service.
    For now, we simulate it.
    """
    logger.info(f"Sending escalation email for {escalation_data['escalation_id']}")
    
    email_subject = f"[ESCALATION] {escalation_data['escalation_id']} - {escalation_data['subject']}"
    confidence = escalation_data.get('confidence', 0.0) or 0.0
    priority_score = escalation_data.get('priority_score', 0) or 0
    email_body = f"""
Escalation ID: {escalation_data['escalation_id']}
Ticket ID: {escalation_data['ticket_id']}
Client: {escalation_data['client_name']}
Email: {escalation_data['client_email']}

Subject: {escalation_data['subject']}
Category: {escalation_data['category']}
Priority: {priority_score}/100
Confidence: {confidence:.2%}

Reason: {escalation_data['reason']}

Context: {escalation_data['context']}

---
Timestamp: {escalation_data['timestamp']}
"""
    
    logger.debug(f"Email subject: {email_subject}")
    logger.debug(f"Email body:\n{email_body}")
    
    # In production, send email here
    # For now, return success
    return True


def get_escalation_status(escalation_id: str) -> Dict:
    """
    Get status of an escalation (simulated).
    """
    return {
        "escalation_id": escalation_id,
        "status": "assigned_to_human",
        "assigned_at": datetime.now().isoformat()
    }
