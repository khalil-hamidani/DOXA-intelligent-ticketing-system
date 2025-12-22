from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.kb import KBUpdateType


class KBDocumentBase(BaseModel):
    title: str
    content: str
    category: Optional[str] = None


class KBDocumentCreate(KBDocumentBase):
    pass


class KBDocumentRead(KBDocumentBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KBSnippetRead(BaseModel):
    id: UUID
    doc_id: UUID
    content: str
    relevance_score: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class KBUpdateCreate(BaseModel):
    ticket_id: Optional[UUID] = None
    change_type: KBUpdateType
    content: str


class KBUpdateRead(KBUpdateCreate):
    id: UUID
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
