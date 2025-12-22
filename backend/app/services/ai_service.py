from sqlalchemy.orm import Session
from app.models.ticket import Ticket, TicketStatus
from app.models.ticket_response import TicketResponse, ResponseSource
from app.schemas.ai import AIAnalyzeTicketRequest
from fastapi import HTTPException
from uuid import UUID


class AIService:
    @staticmethod
    def process_ai_response(db: Session, payload: AIAnalyzeTicketRequest):
        # 1. Validate Ticket Exists
        ticket = db.query(Ticket).filter(Ticket.id == payload.ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        # 2. Create Ticket Response
        # Note: kb_sources are received but not stored as per current locked schema limitations
        response = TicketResponse(
            ticket_id=ticket.id,
            source=ResponseSource.AI,
            content=payload.response,
            confidence=payload.confidence,
        )
        db.add(response)

        # 3. Update Ticket Status & Confidence
        # Only update status if it's currently OPEN.
        # If it's already CLOSED or ESCALATED, we might still want to add the response but not change status.
        if ticket.status == TicketStatus.OPEN:
            ticket.status = TicketStatus.AI_ANSWERED

        # Always update confidence score from the latest analysis
        ticket.ai_confidence = payload.confidence

        db.commit()
        db.refresh(ticket)

        return True
