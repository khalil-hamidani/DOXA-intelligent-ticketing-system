from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class FeedbackBase(BaseModel):
    satisfied: bool
    comment: Optional[str] = None


class FeedbackCreate(FeedbackBase):
    pass


class FeedbackRead(FeedbackBase):
    id: UUID
    ticket_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
