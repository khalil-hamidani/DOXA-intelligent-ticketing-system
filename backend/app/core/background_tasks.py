"""
Background Tasks for AI Integration

Handles asynchronous polling of AI service for ticket processing.
Runs in a separate thread to avoid blocking the main request.
"""

import logging
import threading
import time
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.ticket import Ticket, TicketStatus
from app.models.ticket_response import TicketResponse, ResponseSource
from app.integrations.ai_client import (
    ai_client,
    AIStatus,
    AI_POLL_INTERVAL_SECONDS,
    AI_MAX_POLL_ATTEMPTS,
)

logger = logging.getLogger(__name__)


def get_db_session() -> Session:
    """Create a new database session for background task"""
    return SessionLocal()


def map_ai_status_to_backend(ai_status: AIStatus) -> TicketStatus:
    """
    Map AI status to Backend status.

    | AI Status           | Backend Action                          |
    |---------------------|-----------------------------------------|
    | resolved/answered   | AI_ANSWERED                             |
    | escalated           | ESCALATED                               |
    | waiting_review      | ESCALATED (treat as needs human)        |
    | rejected/invalid    | CLOSED (with rejection message)         |
    | failed              | ESCALATED (fallback to human)           |
    | processing/pending  | Keep as OPEN (still processing)         |
    | unknown             | ESCALATED (safety fallback)             |
    """
    status_map = {
        AIStatus.RESOLVED: TicketStatus.AI_ANSWERED,
        AIStatus.ANSWERED: TicketStatus.AI_ANSWERED,  # AI uses "answered"
        AIStatus.ESCALATED: TicketStatus.ESCALATED,
        AIStatus.WAITING_REVIEW: TicketStatus.ESCALATED,
        AIStatus.REJECTED: TicketStatus.CLOSED,
        AIStatus.INVALID: TicketStatus.CLOSED,  # AI uses "invalid"
        AIStatus.FAILED: TicketStatus.ESCALATED,
        AIStatus.PROCESSING: TicketStatus.OPEN,
        AIStatus.PENDING: TicketStatus.OPEN,
        AIStatus.PENDING_VALIDATION: TicketStatus.OPEN,
        AIStatus.VALIDATED: TicketStatus.OPEN,
        AIStatus.UNKNOWN: TicketStatus.ESCALATED,
    }
    return status_map.get(ai_status, TicketStatus.ESCALATED)


def process_ai_response(
    ticket_id: UUID,
    ai_ticket_id: str,
) -> None:
    """
    Background task to poll AI service and update ticket.

    This function:
    1. Polls AI service for ticket status
    2. Waits until status != processing
    3. Maps AI status to backend status
    4. Creates AI response record
    5. Updates ticket status and confidence

    NEVER raises exceptions - all failures result in escalation.
    """
    logger.info(
        f"[Background] Starting AI polling for ticket {ticket_id}, AI ID: {ai_ticket_id}"
    )

    db: Optional[Session] = None
    attempt = 0

    try:
        while attempt < AI_MAX_POLL_ATTEMPTS:
            attempt += 1
            logger.debug(
                f"[Background] Poll attempt {attempt}/{AI_MAX_POLL_ATTEMPTS} for {ai_ticket_id}"
            )

            # Poll AI service
            ai_response = ai_client.get_ticket_status(ai_ticket_id)

            # Check if still processing (any "in-progress" status)
            processing_statuses = [
                AIStatus.PROCESSING,
                AIStatus.PENDING,
                AIStatus.PENDING_VALIDATION,
                AIStatus.VALIDATED,
            ]
            if ai_response.status in processing_statuses:
                logger.debug(
                    f"[Background] Still processing ({ai_response.status.value}), waiting {AI_POLL_INTERVAL_SECONDS}s..."
                )
                time.sleep(AI_POLL_INTERVAL_SECONDS)
                continue

            # Status changed - process result
            logger.info(f"[Background] AI returned status: {ai_response.status.value}")

            # Get fresh DB session
            db = get_db_session()
            try:
                ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
                if not ticket:
                    logger.error(f"[Background] Ticket {ticket_id} not found in DB")
                    return

                # Only update if ticket is still OPEN
                if ticket.status != TicketStatus.OPEN:
                    logger.info(
                        f"[Background] Ticket {ticket_id} already has status {ticket.status}, skipping"
                    )
                    return

                # Map AI status to backend status
                new_status = map_ai_status_to_backend(ai_response.status)

                logger.info(
                    f"[Background] AI response details - status: {ai_response.status}, solution_text: {ai_response.solution_text[:100] if ai_response.solution_text else 'None'}, message: {ai_response.message[:100] if ai_response.message else 'None'}"
                )

                # Create AI response record if we have solution text
                if ai_response.solution_text:
                    response_content = ai_response.solution_text
                elif ai_response.message:
                    # Use message as fallback for solution_text
                    response_content = ai_response.message
                else:
                    # Fallback messages based on status
                    fallback_messages = {
                        AIStatus.RESOLVED: "Your request has been processed by our AI system.",
                        AIStatus.ANSWERED: "Your request has been processed by our AI system.",
                        AIStatus.ESCALATED: "Your request has been escalated to a human agent for further assistance.",
                        AIStatus.WAITING_REVIEW: "Your request is being reviewed by our support team.",
                        AIStatus.REJECTED: "We couldn't process your request. Please provide more details and try again.",
                        AIStatus.INVALID: "We couldn't process your request. Please provide more details and try again.",
                        AIStatus.FAILED: "We encountered an issue processing your request. A human agent will assist you shortly.",
                    }
                    response_content = fallback_messages.get(
                        ai_response.status,
                        "Your request is being handled by our support team.",
                    )

                # Determine response source
                response_source = ResponseSource.AI

                # Create response record
                ticket_response = TicketResponse(
                    ticket_id=ticket.id,
                    source=response_source,
                    content=response_content,
                    confidence=ai_response.confidence,
                )
                db.add(ticket_response)

                # Update ticket
                ticket.status = new_status

                # Store AI confidence
                if ai_response.confidence is not None:
                    ticket.ai_confidence = ai_response.confidence

                # Update category if AI detected one and ticket doesn't have one
                if ai_response.category and not ticket.category:
                    # Map AI categories to backend categories
                    category_map = {
                        "technique": "TECHNICAL",
                        "technical": "TECHNICAL",
                        "troubleshooting": "TECHNICAL",
                        "facturation": "BILLING",
                        "billing": "BILLING",
                        "authentification": "ACCOUNT",
                        "authentication": "ACCOUNT",
                        "account": "ACCOUNT",
                        "installation": "TECHNICAL",
                        "feature_request": "GENERAL",
                        "bug_report": "TECHNICAL",
                        "autre": "OTHER",
                        "other": "OTHER",
                    }
                    mapped_category = category_map.get(
                        ai_response.category.lower(), ai_response.category.upper()
                    )
                    ticket.category = mapped_category

                db.commit()
                logger.info(
                    f"[Background] Ticket {ticket_id} updated: status={new_status}, confidence={ai_response.confidence}"
                )

            finally:
                db.close()

            # Done processing
            return

        # Max attempts reached - escalate
        logger.warning(
            f"[Background] Max poll attempts reached for {ai_ticket_id}, escalating"
        )
        _escalate_ticket_on_failure(
            ticket_id, "AI processing timeout - max poll attempts reached"
        )

    except Exception as e:
        logger.error(
            f"[Background] Unexpected error processing ticket {ticket_id}: {e}"
        )
        _escalate_ticket_on_failure(ticket_id, f"AI processing error: {str(e)}")
    finally:
        if db:
            try:
                db.close()
            except:
                pass


def _escalate_ticket_on_failure(ticket_id: UUID, reason: str) -> None:
    """
    Escalate ticket when AI processing fails.

    This ensures a human agent will handle the ticket.
    """
    logger.warning(f"[Background] Escalating ticket {ticket_id} due to: {reason}")

    db = None
    try:
        db = get_db_session()
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

        if ticket and ticket.status == TicketStatus.OPEN:
            ticket.status = TicketStatus.ESCALATED

            # Add escalation note as response
            escalation_response = TicketResponse(
                ticket_id=ticket.id,
                source=ResponseSource.AI,
                content=f"This ticket has been automatically escalated to a human agent. Reason: {reason}",
                confidence=0.0,
            )
            db.add(escalation_response)
            db.commit()

            logger.info(f"[Background] Ticket {ticket_id} escalated successfully")
    except Exception as e:
        logger.error(f"[Background] Failed to escalate ticket {ticket_id}: {e}")
    finally:
        if db:
            try:
                db.close()
            except:
                pass


def start_ai_processing(ticket_id: UUID, ai_ticket_id: str) -> None:
    """
    Start background processing for a ticket.

    Spawns a daemon thread that will poll AI service and update ticket.
    Thread is daemon so it won't block application shutdown.
    """
    if not ai_ticket_id:
        logger.warning(
            f"[Background] No AI ticket ID for {ticket_id}, escalating immediately"
        )
        _escalate_ticket_on_failure(ticket_id, "Failed to submit to AI service")
        return

    thread = threading.Thread(
        target=process_ai_response,
        args=(ticket_id, ai_ticket_id),
        daemon=True,
        name=f"ai-poll-{ticket_id}",
    )
    thread.start()
    logger.info(f"[Background] Started polling thread for ticket {ticket_id}")
