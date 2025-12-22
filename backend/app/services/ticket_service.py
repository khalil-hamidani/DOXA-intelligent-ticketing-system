from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.ticket import Ticket, TicketStatus
from app.models.ticket_response import TicketResponse, ResponseSource
from app.schemas.ticket import TicketCreate, TicketUpdateStatus
from app.models.user import User, UserRole
from fastapi import HTTPException, status
from datetime import datetime
import random
import string
from uuid import UUID


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
        return db_ticket

    @staticmethod
    def get_tickets(
        db: Session,
        user: User,
        skip: int = 0,
        limit: int = 100,
        status_filter: TicketStatus = None,
        category_filter: str = None,
    ):
        query = db.query(Ticket)

        if user.role == UserRole.CLIENT:
            query = query.filter(Ticket.client_id == user.id)

        if status_filter:
            query = query.filter(Ticket.status == status_filter)

        if category_filter:
            query = query.filter(Ticket.category == category_filter)

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

        if ticket.status not in [TicketStatus.ESCALATED, TicketStatus.AI_ANSWERED]:
            # While requirements say "Ticket must be ESCALATED or AI_ANSWERED",
            # usually you can close from OPEN too, but we will stick to strict requirements.
            raise HTTPException(
                status_code=400,
                detail="Ticket must be Escalated or AI Answered to close",
            )

        ticket.status = TicketStatus.CLOSED
        ticket.updated_at = datetime.now()

        db.commit()
        db.refresh(ticket)
        return ticket
