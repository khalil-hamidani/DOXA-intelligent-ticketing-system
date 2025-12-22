import enum
import uuid
from sqlalchemy import Column, String, Text, Float, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.types import UserDefinedType
from app.db.base import Base


class Vector(UserDefinedType):
    def get_col_spec(self, **kw):
        return "vector"


class KBUpdateType(str, enum.Enum):
    NEW_DOC = "new_doc"
    ENRICH = "enrich"
    CORRECTION = "correction"


class KBDocument(Base):
    __tablename__ = "kb_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)
    embeddings = Column(Vector, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class KBSnippet(Base):
    __tablename__ = "kb_snippets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doc_id = Column(
        UUID(as_uuid=True),
        ForeignKey("kb_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    content = Column(Text, nullable=False)
    relevance_score = Column(Float, nullable=True)


class KBUpdate(Base):
    __tablename__ = "kb_updates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=True)
    change_type = Column(Enum(KBUpdateType), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
