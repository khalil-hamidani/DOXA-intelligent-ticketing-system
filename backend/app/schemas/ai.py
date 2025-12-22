from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID


class AIAnalyzeTicketRequest(BaseModel):
    ticket_id: UUID
    response: str
    confidence: float
    kb_sources: Optional[List[UUID]] = []


class AIAnalyzeTicketResponse(BaseModel):
    success: bool
