from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core import deps
from app.schemas.ticket import (
    TicketCreate,
    TicketRead,
    TicketDetail,
    TicketUpdateStatus,
    TicketReply,
    TicketResponseRead,
    AttachmentRead,
)
from app.services.ticket_service import TicketService
from app.models.user import User, UserRole
from app.models.ticket import TicketStatus

from app.schemas.feedback import FeedbackCreate, FeedbackRead
from app.services.feedback_service import FeedbackService
import os
import shutil

router = APIRouter()

# Allowed file types
ALLOWED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.gif'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/", response_model=TicketRead)
def create_ticket(
    ticket_in: TicketCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    if current_user.role != UserRole.CLIENT:
        raise HTTPException(status_code=403, detail="Only clients can create tickets")
    return TicketService.create_ticket(
        db=db, ticket_in=ticket_in, client_id=current_user.id
    )


@router.get("/", response_model=List[TicketRead])
def read_tickets(
    skip: int = 0,
    limit: int = 100,
    status: Optional[TicketStatus] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    return TicketService.get_tickets(
        db=db,
        user=current_user,
        skip=skip,
        limit=limit,
        status_filter=status,
        category_filter=category,
        search_query=search,
    )


@router.get("/{ticket_id}", response_model=TicketDetail)
def read_ticket(
    ticket_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    return TicketService.get_ticket(db=db, ticket_id=ticket_id, user=current_user)


@router.patch("/{ticket_id}/status", response_model=TicketRead)
def update_ticket_status(
    ticket_id: UUID,
    status_update: TicketUpdateStatus,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    return TicketService.update_ticket_status(
        db=db, ticket_id=ticket_id, status_update=status_update, user=current_user
    )


@router.post("/{ticket_id}/reply", response_model=TicketResponseRead)
def reply_ticket(
    ticket_id: UUID,
    reply: TicketReply,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    return TicketService.reply_to_ticket(
        db=db, ticket_id=ticket_id, content=reply.content, user=current_user
    )


@router.post("/{ticket_id}/escalate", response_model=TicketRead)
def escalate_ticket(
    ticket_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    return TicketService.escalate_ticket(db=db, ticket_id=ticket_id, user=current_user)


@router.post("/{ticket_id}/close", response_model=TicketRead)
def close_ticket(
    ticket_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    return TicketService.close_ticket(db=db, ticket_id=ticket_id, user=current_user)


@router.post("/{ticket_id}/feedback", response_model=FeedbackRead)
def submit_feedback(
    ticket_id: UUID,
    feedback_in: FeedbackCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    return FeedbackService.create_feedback(
        db=db, ticket_id=ticket_id, feedback_in=feedback_in, user=current_user
    )


@router.get("/{ticket_id}/feedback", response_model=Optional[FeedbackRead])
def read_feedback(
    ticket_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Get feedback for a ticket. Returns null if no feedback exists yet."""
    try:
        return FeedbackService.get_feedback(db=db, ticket_id=ticket_id, user=current_user)
    except HTTPException as e:
        if e.status_code == 404 and "Feedback not found" in str(e.detail):
            return None  # No feedback yet - this is normal
        raise  # Re-raise other errors (ticket not found, permission denied)


@router.post("/{ticket_id}/attachments", response_model=AttachmentRead)
async def upload_attachment(
    ticket_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Upload an attachment to a ticket (images and PDFs only)"""
    # Check file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check file size (read content to check)
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Reset file position
    await file.seek(0)
    
    return TicketService.add_attachment(
        db=db,
        ticket_id=ticket_id,
        file=file,
        file_content=content,
        user=current_user
    )


@router.get("/{ticket_id}/attachments", response_model=List[AttachmentRead])
def get_attachments(
    ticket_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Get all attachments for a ticket"""
    return TicketService.get_attachments(db=db, ticket_id=ticket_id, user=current_user)


@router.get("/{ticket_id}/attachments/{attachment_id}/download")
def download_attachment(
    ticket_id: UUID,
    attachment_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Download a specific attachment"""
    attachment = TicketService.get_attachment(
        db=db, ticket_id=ticket_id, attachment_id=attachment_id, user=current_user
    )
    
    if not os.path.exists(attachment.file_path):
        raise HTTPException(status_code=404, detail="File not found on server")
    
    return FileResponse(
        path=attachment.file_path,
        filename=attachment.original_filename,
        media_type=attachment.file_type
    )
