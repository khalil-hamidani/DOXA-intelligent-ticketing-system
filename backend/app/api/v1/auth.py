from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core import deps, security
from app.models.user import User, UserRole
from app.schemas.auth import Login, Register, Token
from app.schemas.user import User as UserSchema

router = APIRouter()


class ProfileUpdate(BaseModel):
    password: Optional[str] = None
    language: Optional[str] = None
    profile_picture_url: Optional[str] = None


@router.post("/register", response_model=UserSchema)
def register(
    *,
    db: Session = Depends(deps.get_db),
    user_in: Register,
) -> Any:
    """
    Create new user (CLIENT only).
    """
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )

    user = User(
        email=user_in.email,
        password_hash=security.get_password_hash(user_in.password),
        role=UserRole.CLIENT,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(
    *,
    db: Session = Depends(deps.get_db),
    user_in: Login,
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not security.verify_password(user_in.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token = security.create_access_token(subject=user.id, role=user.role.value)
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserSchema)
def read_users_me(
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current user.
    """
    return current_user


@router.put("/me", response_model=UserSchema)
def update_users_me(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    profile_update: ProfileUpdate,
) -> Any:
    """
    Update current user profile.
    """
    if profile_update.password:
        current_user.password_hash = security.get_password_hash(profile_update.password)

    if profile_update.language is not None:
        current_user.language = profile_update.language

    if profile_update.profile_picture_url is not None:
        current_user.profile_picture_url = (
            profile_update.profile_picture_url
            if profile_update.profile_picture_url
            else None
        )

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user
