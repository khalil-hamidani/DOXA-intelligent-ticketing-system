import enum
import uuid
from sqlalchemy import (
    Column,
    String,
    Text,
    Float,
    DateTime,
    Enum,
    ForeignKey,
    BigInteger,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class TicketStatus(str, enum.Enum):
    OPEN = "OPEN"
    AI_ANSWERED = "AI_ANSWERED"
    ESCALATED = "ESCALATED"
    CLOSED = "CLOSED"


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reference = Column(String(20), unique=True, nullable=False)
    client_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    assigned_agent_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)
    status = Column(Enum(TicketStatus), default=TicketStatus.OPEN)
    ai_confidence = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    client = relationship("app.models.user.User", foreign_keys=[client_id])
    assigned_agent = relationship(
        "app.models.user.User", foreign_keys=[assigned_agent_id]
    )
    attachments = relationship("TicketAttachment", back_populates="ticket", cascade="all, delete-orphan")


class TicketAttachment(Base):
    __tablename__ = "ticket_attachments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=False)
    filename = Column(String(255), nullable=False)  # Stored filename
    original_filename = Column(String(255), nullable=False)  # Original uploaded name
    file_path = Column(Text, nullable=False)  # Full path to file
    file_type = Column(String(50), nullable=True)  # MIME type
    file_size = Column(BigInteger, nullable=True)  # Size in bytes
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    ticket = relationship("Ticket", back_populates="attachments")
