from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.kb import KBDocument, KBSnippet, KBUpdate
from app.schemas.kb import KBDocumentCreate, KBDocumentUpdate, KBUpdateCreate
from app.models.user import User, UserRole
from fastapi import HTTPException
from uuid import UUID


class KBService:
    @staticmethod
    def create_document(
        db: Session, doc_in: KBDocumentCreate, user: User
    ) -> KBDocument:
        if user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=403, detail="Only admins can create KB documents"
            )

        db_doc = KBDocument(
            title=doc_in.title,
            content=doc_in.content,
            category=doc_in.category,
            embeddings=None,  # Explicitly NULL as per requirements
        )
        db.add(db_doc)
        db.commit()
        db.refresh(db_doc)
        return db_doc

    @staticmethod
    def get_documents(
        db: Session,
        user: User,
        skip: int = 0,
        limit: int = 100,
        category: str = None,
        keyword: str = None,
    ):
        if user.role not in [UserRole.AGENT, UserRole.ADMIN]:
            raise HTTPException(
                status_code=403, detail="Not authorized to view KB documents"
            )

        query = db.query(KBDocument)

        if category:
            query = query.filter(KBDocument.category == category)

        if keyword:
            query = query.filter(KBDocument.title.ilike(f"%{keyword}%"))

        query = query.order_by(desc(KBDocument.created_at))
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def get_document(db: Session, doc_id: UUID, user: User):
        if user.role not in [UserRole.AGENT, UserRole.ADMIN]:
            raise HTTPException(
                status_code=403, detail="Not authorized to view KB documents"
            )

        doc = db.query(KBDocument).filter(KBDocument.id == doc_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return doc

    @staticmethod
    def update_document(
        db: Session, doc_id: UUID, doc_update: KBDocumentUpdate, user: User
    ) -> KBDocument:
        if user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=403, detail="Only admins can update KB documents"
            )

        doc = db.query(KBDocument).filter(KBDocument.id == doc_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        update_data = doc_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(doc, field, value)

        db.commit()
        db.refresh(doc)
        return doc

    @staticmethod
    def delete_document(db: Session, doc_id: UUID, user: User) -> bool:
        if user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=403, detail="Only admins can delete KB documents"
            )

        doc = db.query(KBDocument).filter(KBDocument.id == doc_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Delete associated snippets first
        db.query(KBSnippet).filter(KBSnippet.doc_id == doc_id).delete()
        db.delete(doc)
        db.commit()
        return True

    @staticmethod
    def get_snippets(db: Session, user: User, skip: int = 0, limit: int = 100):
        # Accessible by AI service (which we assume acts as ADMIN or has special role) or ADMIN
        if user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=403, detail="Only admins or AI service can view snippets"
            )

        return db.query(KBSnippet).offset(skip).limit(limit).all()

    @staticmethod
    def create_update(db: Session, update_in: KBUpdateCreate, user: User):
        if user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=403,
                detail="Only admins or AI service can submit KB updates",
            )

        db_update = KBUpdate(
            ticket_id=update_in.ticket_id,
            change_type=update_in.change_type,
            content=update_in.content,
        )
        db.add(db_update)
        db.commit()
        db.refresh(db_update)
        return db_update
