from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core import deps
from app.schemas.ticket import (
    TicketCreate,
    TicketRead,
    TicketDetail,
    TicketUpdateStatus,
)
from app.services.ticket_service import TicketService
from app.models.user import User, UserRole
from app.models.ticket import TicketStatus

router = APIRouter()


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
