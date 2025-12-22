from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core import deps
from app.schemas.metrics import MetricsOverview
from app.services.metrics_service import MetricsService
from app.models.user import User

router = APIRouter()


@router.get("/overview", response_model=MetricsOverview)
def read_metrics_overview(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    return MetricsService.get_overview(db=db, user=current_user)
