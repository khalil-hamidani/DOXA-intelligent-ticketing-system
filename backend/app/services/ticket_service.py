import logging
import os
import random
import string
import uuid as uuid_module
from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, status, UploadFile
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.ticket import Ticket, TicketStatus, TicketAttachment
from app.models.ticket_response import TicketResponse, ResponseSource
from app.models.user import User, UserRole
from app.schemas.ticket import TicketCreate, TicketUpdateStatus
from app.integrations.ai_client import ai_client, AI_ENABLED
from app.core.background_tasks import start_ai_processing

logger = logging.getLogger(__name__)

# Base directory for attachments
ATTACHMENTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "attachments"
)


class TicketService:
    @staticmethod
    def generate_reference(db: Session) -> str:
        year = datetime.now().year
        # Try to generate a unique reference
        for _ in range(10):
            suffix = "".join(
                random.choices(string.ascii_uppercase + string.digits, k=4)
            )
            ref = f"REF-{year}-{suffix}"
            if not db.query(Ticket).filter(Ticket.reference == ref).first():
                return ref
        raise HTTPException(
            status_code=500, detail="Could not generate unique ticket reference"
        )

    @staticmethod
    def create_ticket(db: Session, ticket_in: TicketCreate, client_id: int) -> Ticket:
        reference = TicketService.generate_reference(db)
        db_ticket = Ticket(
            reference=reference,
            subject=ticket_in.subject,
            description=ticket_in.description,
            category=ticket_in.category,
            client_id=client_id,
            status=TicketStatus.OPEN,
        )
        db.add(db_ticket)
        db.commit()
        db.refresh(db_ticket)

        # ─────────────────────────────────────────────────────────────────────
        # AI INTEGRATION: Submit ticket to AI service for processing
        # This is NON-BLOCKING - we immediately return the ticket to the user
        # while AI processes in the background
        # ─────────────────────────────────────────────────────────────────────
        if AI_ENABLED:
            try:
                logger.info(f"Submitting ticket {db_ticket.id} to AI service")

                # Submit to AI service
                ai_response = ai_client.submit_ticket(
                    ticket_id=str(db_ticket.id),
                    subject=db_ticket.subject,
                    description=db_ticket.description,
                    category=db_ticket.category,
                    language=getattr(ticket_in, "language", "en"),  # Default to English
                )

                # Start background polling if AI accepted the ticket
                if ai_response.ai_ticket_id:
                    logger.info(
                        f"AI accepted ticket, AI ID: {ai_response.ai_ticket_id}"
                    )
                    start_ai_processing(db_ticket.id, ai_response.ai_ticket_id)
                else:
                    # AI did not return a ticket ID - escalate immediately
                    logger.warning(
                        f"AI did not accept ticket {db_ticket.id}, escalating"
                    )
                    db_ticket.status = TicketStatus.ESCALATED
                    db.commit()
                    db.refresh(db_ticket)

            except Exception as e:
                # On ANY error, escalate the ticket and continue
                # NEVER let AI issues block ticket creation
                logger.error(f"Failed to submit ticket to AI: {e}")
                db_ticket.status = TicketStatus.ESCALATED
                db.commit()
                db.refresh(db_ticket)
        else:
            logger.info(f"AI integration disabled, ticket {db_ticket.id} stays OPEN")

        return db_ticket

    @staticmethod
    def get_tickets(
        db: Session,
        user: User,
        skip: int = 0,
        limit: int = 100,
        status_filter: TicketStatus = None,
        category_filter: str = None,
        search_query: str = None,
    ):
        query = db.query(Ticket)

        if user.role == UserRole.CLIENT:
            query = query.filter(Ticket.client_id == user.id)

        if status_filter:
            query = query.filter(Ticket.status == status_filter)

        if category_filter:
            query = query.filter(Ticket.category == category_filter)

        if search_query:
            search_term = f"%{search_query}%"
            query = query.filter(
                (Ticket.reference.ilike(search_term))
                | (Ticket.subject.ilike(search_term))
            )

        query = query.order_by(desc(Ticket.created_at))
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def get_ticket(db: Session, ticket_id: UUID, user: User):
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        if user.role == UserRole.CLIENT and ticket.client_id != user.id:
            raise HTTPException(
                status_code=403, detail="Not authorized to access this ticket"
            )

        # Fetch responses manually since relationship is missing
        responses = (
            db.query(TicketResponse)
            .filter(TicketResponse.ticket_id == ticket.id)
            .order_by(TicketResponse.created_at)
            .all()
        )

        # Dynamically attach responses for Pydantic schema
        ticket.responses = responses
        return ticket

    @staticmethod
    def update_ticket_status(
        db: Session, ticket_id: UUID, status_update: TicketUpdateStatus, user: User
    ):
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        # Only AGENT or AI (which we assume acts as AGENT or has special permissions)
        if user.role not in [UserRole.AGENT, UserRole.ADMIN]:
            raise HTTPException(
                status_code=403, detail="Only agents can update ticket status"
            )

        current_status = ticket.status
        new_status = status_update.status

        # Allowed transitions
        valid_transitions = {
            TicketStatus.OPEN: [TicketStatus.AI_ANSWERED, TicketStatus.ESCALATED],
            TicketStatus.AI_ANSWERED: [TicketStatus.ESCALATED],
            TicketStatus.ESCALATED: [TicketStatus.CLOSED],
            TicketStatus.CLOSED: [],  # No transitions from CLOSED
        }

        # Allow same status update? Usually yes, or no-op.
        if current_status != new_status:
            if new_status not in valid_transitions.get(current_status, []):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status transition from {current_status} to {new_status}",
                )

            ticket.status = new_status

            # Optionally assign agent when ESCALATED
            if new_status == TicketStatus.ESCALATED and not ticket.assigned_agent_id:
                ticket.assigned_agent_id = user.id

            db.commit()
            db.refresh(ticket)

        return ticket

    @staticmethod
    def reply_to_ticket(db: Session, ticket_id: UUID, content: str, user: User):
        if user.role not in [UserRole.AGENT, UserRole.ADMIN]:
            raise HTTPException(
                status_code=403, detail="Only agents can reply to tickets"
            )

        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        if ticket.status == TicketStatus.CLOSED:
            raise HTTPException(
                status_code=400, detail="Cannot reply to a closed ticket"
            )

        response = TicketResponse(
            ticket_id=ticket.id,
            source=ResponseSource.HUMAN,
            content=content,
            confidence=None,
        )
        db.add(response)

        # Update ticket updated_at
        ticket.updated_at = datetime.now()

        db.commit()
        db.refresh(response)
        return response

    @staticmethod
    def escalate_ticket(db: Session, ticket_id: UUID, user: User):
        if user.role not in [UserRole.AGENT, UserRole.ADMIN]:
            raise HTTPException(
                status_code=403, detail="Only agents can escalate tickets"
            )

        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        if ticket.status not in [TicketStatus.OPEN, TicketStatus.AI_ANSWERED]:
            raise HTTPException(
                status_code=400, detail="Ticket cannot be escalated from current status"
            )

        ticket.status = TicketStatus.ESCALATED
        ticket.assigned_agent_id = user.id
        ticket.updated_at = datetime.now()

        db.commit()
        db.refresh(ticket)
        return ticket

    @staticmethod
    def close_ticket(db: Session, ticket_id: UUID, user: User):
        if user.role not in [UserRole.AGENT, UserRole.ADMIN]:
            raise HTTPException(status_code=403, detail="Only agents can close tickets")

        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        if ticket.status == TicketStatus.CLOSED:
            raise HTTPException(status_code=400, detail="Ticket is already closed")

        # Allow closing from any non-closed status
        ticket.status = TicketStatus.CLOSED
        ticket.updated_at = datetime.now()

        db.commit()
        db.refresh(ticket)
        return ticket

    @staticmethod
    def add_attachment(
        db: Session, ticket_id: UUID, file: UploadFile, file_content: bytes, user: User
    ) -> TicketAttachment:
        """Add an attachment to a ticket"""
        # Get ticket and verify access
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        # Only ticket owner or agents/admins can add attachments
        if user.role == UserRole.CLIENT and ticket.client_id != user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Create directory for this ticket's attachments
        ticket_dir = os.path.join(ATTACHMENTS_DIR, ticket.reference)
        os.makedirs(ticket_dir, exist_ok=True)

        # Generate unique filename
        file_ext = os.path.splitext(file.filename)[1].lower()
        unique_filename = f"{uuid_module.uuid4()}{file_ext}"
        file_path = os.path.join(ticket_dir, unique_filename)

        # Save file
        with open(file_path, "wb") as f:
            f.write(file_content)

        # Create attachment record
        attachment = TicketAttachment(
            ticket_id=ticket_id,
            filename=unique_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_type=file.content_type,
            file_size=len(file_content),
        )

        db.add(attachment)
        db.commit()
        db.refresh(attachment)

        return attachment

    @staticmethod
    def get_attachments(db: Session, ticket_id: UUID, user: User) -> list:
        """Get all attachments for a ticket"""
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        # Check access
        if user.role == UserRole.CLIENT and ticket.client_id != user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

        return (
            db.query(TicketAttachment)
            .filter(TicketAttachment.ticket_id == ticket_id)
            .all()
        )

    @staticmethod
    def get_attachment(
        db: Session, ticket_id: UUID, attachment_id: UUID, user: User
    ) -> TicketAttachment:
        """Get a specific attachment"""
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        # Check access
        if user.role == UserRole.CLIENT and ticket.client_id != user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

        attachment = (
            db.query(TicketAttachment)
            .filter(
                TicketAttachment.id == attachment_id,
                TicketAttachment.ticket_id == ticket_id,
            )
            .first()
        )

        if not attachment:
            raise HTTPException(status_code=404, detail="Attachment not found")

        return attachment
