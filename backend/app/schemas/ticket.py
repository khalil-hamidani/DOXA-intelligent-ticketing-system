from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.ticket import TicketStatus
from app.models.ticket_response import ResponseSource


class TicketResponseRead(BaseModel):
    id: UUID
    source: ResponseSource
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TicketBase(BaseModel):
    subject: str
    description: str
    category: Optional[str] = None


class TicketCreate(TicketBase):
    pass


class TicketUpdateStatus(BaseModel):
    status: TicketStatus


class TicketReply(BaseModel):
    content: str


class TicketRead(TicketBase):
    id: UUID
    reference: str
    status: TicketStatus
    client_id: int
    assigned_agent_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TicketDetail(TicketRead):
    responses: List[TicketResponseRead] = []
