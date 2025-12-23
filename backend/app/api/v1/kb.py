from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core import deps
from app.schemas.kb import (
    KBDocumentCreate,
    KBDocumentRead,
    KBDocumentUpdate,
    KBSnippetRead,
    KBUpdateCreate,
    KBUpdateRead,
)
from app.services.kb_service import KBService
from app.models.user import User

router = APIRouter()


@router.post("/documents", response_model=KBDocumentRead)
def create_document(
    doc_in: KBDocumentCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    return KBService.create_document(db=db, doc_in=doc_in, user=current_user)


@router.get("/documents", response_model=List[KBDocumentRead])
def read_documents(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    return KBService.get_documents(
        db=db,
        user=current_user,
        skip=skip,
        limit=limit,
        category=category,
        keyword=keyword,
    )


@router.get("/documents/{doc_id}", response_model=KBDocumentRead)
def read_document(
    doc_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    return KBService.get_document(db=db, doc_id=doc_id, user=current_user)


@router.put("/documents/{doc_id}", response_model=KBDocumentRead)
def update_document(
    doc_id: UUID,
    doc_update: KBDocumentUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    return KBService.update_document(
        db=db, doc_id=doc_id, doc_update=doc_update, user=current_user
    )


@router.delete("/documents/{doc_id}")
def delete_document(
    doc_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    KBService.delete_document(db=db, doc_id=doc_id, user=current_user)
    return {"message": "Document deleted successfully"}


@router.get("/snippets", response_model=List[KBSnippetRead])
def read_snippets(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    return KBService.get_snippets(db=db, user=current_user, skip=skip, limit=limit)


@router.post("/updates", response_model=KBUpdateRead)
def create_kb_update(
    update_in: KBUpdateCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    return KBService.create_update(db=db, update_in=update_in, user=current_user)
