from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.ticket import Ticket, TicketStatus
from app.models.feedback import TicketFeedback
from app.schemas.metrics import MetricsOverview
from app.models.user import User, UserRole
from fastapi import HTTPException


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
                ai_answered_percentage=0.0,
                escalation_rate=0.0,
                satisfaction_rate=0.0,
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

        # 4. Satisfaction Rate
        feedbacks = db.query(TicketFeedback).all()
        total_feedback = len(feedbacks)
        if total_feedback > 0:
            satisfied_count = sum(1 for f in feedbacks if f.satisfied)
            satisfaction_rate = (satisfied_count / total_feedback) * 100
        else:
            satisfaction_rate = 0.0

        # 5. Tickets by Category
        # Group by category
        category_counts = (
            db.query(Ticket.category, func.count(Ticket.id))
            .group_by(Ticket.category)
            .all()
        )

        tickets_by_category = {
            (cat if cat else "Uncategorized"): count for cat, count in category_counts
        }

        return MetricsOverview(
            total_tickets=total_tickets,
            ai_answered_percentage=round(ai_answered_percentage, 2),
            escalation_rate=round(escalation_rate, 2),
            satisfaction_rate=round(satisfaction_rate, 2),
            tickets_by_category=tickets_by_category,
        )
