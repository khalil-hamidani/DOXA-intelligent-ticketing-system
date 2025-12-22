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
    negative_sentiment: Optional[bool] = False
    snippets: Optional[List[str]] = []
    solution_text: Optional[str] = None
    solution_confidence: Optional[float] = None
    severity: Optional[str] = None
    treatment_type: Optional[str] = None
    priority_level: Optional[str] = None
    entities: Optional[List[str]] = []
    response: Optional[str] = None
    escalation_id: Optional[str] = None
    client_email: Optional[str] = None

class Feedback(BaseModel):
    ticket_id: str
    satisfied: bool
    reason: Optional[str] = None
