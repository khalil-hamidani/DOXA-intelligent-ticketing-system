from pydantic import BaseModel, Field
from typing import List, Optional

class Ticket(BaseModel):
    id: str
    client_name: str
    email: str
    subject: str
    description: str
    keywords: Optional[List[str]] = []
    priority_score: Optional[int] = None
    category: Optional[str] = None
    status: str = "pending_validation"
    attempts: int = 0
    # Additional fields used by agents
    summary: Optional[str] = None
    reformulation: Optional[str] = None
    confidence: Optional[float] = None
    escalation_context: Optional[str] = None
    sensitive: Optional[bool] = False
    snippets: Optional[List[str]] = []

class Feedback(BaseModel):
    ticket_id: str
    satisfied: bool
    reason: Optional[str] = None
