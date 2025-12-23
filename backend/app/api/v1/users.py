from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core import deps
from app.schemas.user import User as UserSchema
from app.models.user import User, UserRole

router = APIRouter()


@router.get("/", response_model=List[UserSchema])
def list_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[str] = Query(
        None, description="Filter by role: CLIENT, AGENT, or ADMIN"
    ),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    List all users. Only accessible by admins.
    Optionally filter by role.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can view users list")

    query = db.query(User)

    if role:
        try:
            role_enum = UserRole(role.upper())
            query = query.filter(User.role == role_enum)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid role. Must be one of: CLIENT, AGENT, ADMIN",  # noqa: F541
            )

    query = query.order_by(desc(User.created_at))
    return query.offset(skip).limit(limit).all()


@router.get("/stats")
def get_user_stats(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Get user statistics by role. Only accessible by admins.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403, detail="Only admins can view user statistics"
        )

    total = db.query(User).count()
    clients = db.query(User).filter(User.role == UserRole.CLIENT).count()
    agents = db.query(User).filter(User.role == UserRole.AGENT).count()
    admins = db.query(User).filter(User.role == UserRole.ADMIN).count()
    active = db.query(User).filter(User.is_active == True).count()  # noqa: E712

    return {
        "total": total,
        "by_role": {"CLIENT": clients, "AGENT": agents, "ADMIN": admins},
        "active": active,
        "inactive": total - active,
    }
