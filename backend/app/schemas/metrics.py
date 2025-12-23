from pydantic import BaseModel
from typing import Dict


class MetricsOverview(BaseModel):
    total_tickets: int
    ai_resolution_rate: float  # 0.0-1.0 scale
    avg_response_time_minutes: float
    avg_satisfaction_rating: float  # 0.0-5.0 scale (based on satisfied/not satisfied)
    tickets_by_status: Dict[str, int]
    tickets_by_category: Dict[str, int]
