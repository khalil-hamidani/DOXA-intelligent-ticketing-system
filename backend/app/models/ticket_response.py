import enum
import uuid
from sqlalchemy import Column, Text, Float, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base


class ResponseSource(str, enum.Enum):
    AI = "AI"
    HUMAN = "HUMAN"


class TicketResponse(Base):
    __tablename__ = "ticket_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=False)
    source = Column(Enum(ResponseSource), nullable=False)
    content = Column(Text, nullable=False)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
