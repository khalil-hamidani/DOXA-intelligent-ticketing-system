from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.ticket import Ticket, TicketStatus
from app.models.feedback import TicketFeedback
from app.models.ticket_response import TicketResponse
from app.schemas.metrics import MetricsOverview
from app.models.user import User, UserRole
from fastapi import HTTPException
from datetime import datetime


class MetricsService:
    @staticmethod
    def get_overview(db: Session, user: User) -> MetricsOverview:
        if user.role not in [UserRole.AGENT, UserRole.ADMIN]:
            raise HTTPException(
                status_code=403, detail="Not authorized to view metrics"
            )

        # 1. Total Tickets
        total_tickets = db.query(Ticket).count()

        if total_tickets == 0:
            return MetricsOverview(
                total_tickets=0,
                ai_resolution_rate=0.0,
                avg_response_time_minutes=0.0,
                avg_satisfaction_rating=0.0,
                tickets_by_status={},
                tickets_by_category={},
            )

        # 2. AI Answered Percentage
        # We define this as tickets that are currently in AI_ANSWERED status
        # OR tickets that are CLOSED and have NO assigned agent (implying AI resolved it)
        ai_answered_count = (
            db.query(Ticket)
            .filter(
                (Ticket.status == TicketStatus.AI_ANSWERED)
                | (
                    (Ticket.status == TicketStatus.CLOSED)
                    & (Ticket.assigned_agent_id == None)
                )
            )
            .count()
        )

        ai_answered_percentage = (ai_answered_count / total_tickets) * 100

        # 3. Escalation Rate
        # We define this as tickets that are currently ESCALATED
        # OR tickets that are CLOSED and HAVE an assigned agent
        escalated_count = (
            db.query(Ticket)
            .filter(
                (Ticket.status == TicketStatus.ESCALATED)
                | (
                    (Ticket.status == TicketStatus.CLOSED)
                    & (Ticket.assigned_agent_id != None)
                )
            )
            .count()
        )

        escalation_rate = (escalated_count / total_tickets) * 100

        # 4. Satisfaction Rating (convert satisfied boolean to 5-star scale)
        # satisfied=True -> 5 stars, satisfied=False -> 1 star
        feedbacks = db.query(TicketFeedback).all()
        total_feedback = len(feedbacks)
        if total_feedback > 0:
            # Convert boolean to star rating: True=5, False=1
            total_stars = sum(5 if f.satisfied else 1 for f in feedbacks)
            avg_satisfaction_rating = total_stars / total_feedback
        else:
            avg_satisfaction_rating = 0.0

        # 5. Average Response Time (time from ticket creation to first response)
        avg_response_time_minutes = 0.0
        tickets_with_responses = (
            db.query(
                Ticket, func.min(TicketResponse.created_at).label("first_response")
            )
            .join(TicketResponse, Ticket.id == TicketResponse.ticket_id)
            .group_by(Ticket.id)
            .all()
        )
        if tickets_with_responses:
            total_minutes = 0.0
            for ticket, first_response in tickets_with_responses:
                if first_response and ticket.created_at:
                    delta = first_response - ticket.created_at
                    total_minutes += delta.total_seconds() / 60
            avg_response_time_minutes = total_minutes / len(tickets_with_responses)

        # 6. Tickets by Status
        status_counts = (
            db.query(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status).all()
        )
        tickets_by_status = {status.value: count for status, count in status_counts}

        # 7. Tickets by Category
        category_counts = (
            db.query(Ticket.category, func.count(Ticket.id))
            .group_by(Ticket.category)
            .all()
        )

        tickets_by_category = {
            (cat if cat else "Uncategorized"): count for cat, count in category_counts
        }

        # AI Resolution Rate (0.0-1.0 scale)
        ai_resolution_rate = ai_answered_count / total_tickets

        return MetricsOverview(
            total_tickets=total_tickets,
            ai_resolution_rate=round(ai_resolution_rate, 4),
            avg_response_time_minutes=round(avg_response_time_minutes, 1),
            avg_satisfaction_rating=round(avg_satisfaction_rating, 2),
            tickets_by_status=tickets_by_status,
            tickets_by_category=tickets_by_category,
        )
