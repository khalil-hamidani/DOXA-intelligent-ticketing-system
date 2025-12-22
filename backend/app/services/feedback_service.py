from sqlalchemy.orm import Session
from app.models.feedback import TicketFeedback
from app.models.ticket import Ticket, TicketStatus
from app.schemas.feedback import FeedbackCreate
from app.models.user import User, UserRole
from fastapi import HTTPException
from uuid import UUID


class FeedbackService:
    @staticmethod
    def create_feedback(
        db: Session, ticket_id: UUID, feedback_in: FeedbackCreate, user: User
    ) -> TicketFeedback:
        # 1. Check User Role
        if user.role != UserRole.CLIENT:
            raise HTTPException(
                status_code=403, detail="Only clients can submit feedback"
            )

        # 2. Get Ticket
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        # 3. Check Ownership
        if ticket.client_id != user.id:
            raise HTTPException(
                status_code=403,
                detail="You can only submit feedback for your own tickets",
            )

        # 4. Check Status
        if ticket.status != TicketStatus.CLOSED:
            raise HTTPException(
                status_code=400,
                detail="Feedback can only be submitted for CLOSED tickets",
            )

        # 5. Check Duplicate
        existing_feedback = (
            db.query(TicketFeedback)
            .filter(TicketFeedback.ticket_id == ticket_id)
            .first()
        )
        if existing_feedback:
            raise HTTPException(
                status_code=400, detail="Feedback already submitted for this ticket"
            )

        # 6. Create Feedback
        db_feedback = TicketFeedback(
            ticket_id=ticket_id,
            satisfied=feedback_in.satisfied,
            comment=feedback_in.comment,
        )
        db.add(db_feedback)
        db.commit()
        db.refresh(db_feedback)
        return db_feedback

    @staticmethod
    def get_feedback(db: Session, ticket_id: UUID, user: User) -> TicketFeedback:
        # 1. Check Ticket Existence
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        # 2. Check Permissions
        # Agents/Admins can view any feedback
        # Clients can only view feedback for their own tickets
        if user.role == UserRole.CLIENT and ticket.client_id != user.id:
            raise HTTPException(
                status_code=403,
                detail="You can only view feedback for your own tickets",
            )

        # 3. Get Feedback
        feedback = (
            db.query(TicketFeedback)
            .filter(TicketFeedback.ticket_id == ticket_id)
            .first()
        )
        if not feedback:
            raise HTTPException(
                status_code=404, detail="Feedback not found for this ticket"
            )

        return feedback
