"""
API FastAPI pour le système de ticketing IA
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime

from models.schemas import Ticket, Feedback, TicketStatus
from agents.orchestrator import orchestrator
from kb.kb_manager import kb_manager
from loguru import logger

# Configuration logging
logger.add("logs/app.log", rotation="1 day", retention="7 days")

app = FastAPI(
    title="AI Ticketing System",
    description="Système de ticketing automatisé avec agents IA",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stockage en mémoire (remplacer par DB en production)
tickets_db = {}

# ============ MODELS ============

class TicketCreate(BaseModel):
    client_name: str
    email: str
    subject: str
    description: str

class FeedbackSubmit(BaseModel):
    satisfied: bool
    reason: Optional[str] = None

# ============ ROUTES ============

@app.get("/")
def root():
    """Health check"""
    return {
        "status": "online",
        "service": "AI Ticketing System",
        "version": "1.0.0"
    }

@app.post("/tickets")
def create_ticket(ticket_data: TicketCreate):
    """Crée et traite un nouveau ticket"""
    
    # Créer le ticket
    ticket = Ticket(
        id=str(uuid.uuid4()),
        client_name=ticket_data.client_name,
        email=ticket_data.email,
        subject=ticket_data.subject,
        description=ticket_data.description,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # Sauvegarder
    tickets_db[ticket.id] = ticket
    
    logger.info(f"📝 New ticket created: {ticket.id}")
    
    # Traiter immédiatement
    try:
        result = orchestrator.process_ticket(ticket)
        
        # Mettre à jour le ticket
        tickets_db[ticket.id] = ticket
        
        return {
            "ticket_id": ticket.id,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Error processing ticket {ticket.id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: str):
    """Récupère les détails d'un ticket"""
    
    if ticket_id not in tickets_db:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    ticket = tickets_db[ticket_id]
    return {
        "ticket": ticket.dict(),
        "status": ticket.status.value
    }

@app.post("/tickets/{ticket_id}/feedback")
def submit_feedback(ticket_id: str, feedback_data: FeedbackSubmit):
    """Soumet un feedback client"""
    
    if ticket_id not in tickets_db:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    ticket = tickets_db[ticket_id]
    
    feedback = Feedback(
        ticket_id=ticket_id,
        satisfied=feedback_data.satisfied,
        reason=feedback_data.reason,
        timestamp=datetime.now()
    )
    
    logger.info(f"📬 Feedback received for ticket {ticket_id}")
    
    try:
        result = orchestrator.handle_feedback(ticket, feedback)
        
        # Mettre à jour
        tickets_db[ticket_id] = ticket
        
        return result
        
    except Exception as e:
        logger.error(f"Error handling feedback for {ticket_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/kb/stats")
def kb_stats():
    """Statistiques de la Knowledge Base"""
    return kb_manager.get_stats()

@app.post("/kb/documents")
def add_kb_document(doc_id: str, text: str, metadata: Optional[dict] = None):
    """Ajoute un document à la KB"""
    
    success = kb_manager.add_document(doc_id, text, metadata)
    
    if success:
        return {"success": True, "doc_id": doc_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to add document")

@app.get("/tickets")
def list_tickets(status: Optional[str] = None):
    """Liste tous les tickets (optionnel: filtre par statut)"""
    
    tickets = list(tickets_db.values())
    
    if status:
        tickets = [t for t in tickets if t.status.value == status]
    
    return {
        "total": len(tickets),
        "tickets": [
            {
                "id": t.id,
                "client_name": t.client_name,
                "subject": t.subject,
                "status": t.status.value,
                "priority_score": t.priority_score,
                "escalated": t.escalated,
                "created_at": t.created_at.isoformat()
            }
            for t in tickets
        ]
    }

if __name__ == "__main__":
    import uvicorn
    from config.settings import settings
    
    logger.info("🚀 Starting AI Ticketing System API")
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
