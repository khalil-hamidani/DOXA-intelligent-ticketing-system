import uuid
from sqlalchemy import Column, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base


class TicketFeedback(Base):
    __tablename__ = "ticket_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id = Column(
        UUID(as_uuid=True), ForeignKey("tickets.id"), unique=True, nullable=False
    )
    satisfied = Column(Boolean, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
