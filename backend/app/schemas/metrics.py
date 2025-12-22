from pydantic import BaseModel
from typing import Dict


class MetricsOverview(BaseModel):
    total_tickets: int
    ai_answered_percentage: float
    escalation_rate: float
    satisfaction_rate: float
    tickets_by_category: Dict[str, int]
