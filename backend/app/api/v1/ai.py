from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core import deps
from app.schemas.ai import AIAnalyzeTicketRequest, AIAnalyzeTicketResponse
from app.services.ai_service import AIService

router = APIRouter()


@router.post("/analyze-ticket", response_model=AIAnalyzeTicketResponse)
def analyze_ticket(
    payload: AIAnalyzeTicketRequest,
    db: Session = Depends(deps.get_db),
    # Note: In a real scenario, we would secure this endpoint with a specific API Key or Service Token.
    # For this hackathon scope, we assume the AI service is trusted or internal network restricted.
):
    AIService.process_ai_response(db=db, payload=payload)
    return AIAnalyzeTicketResponse(success=True)
