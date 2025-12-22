from fastapi import APIRouter
from app.api.v1 import auth, tickets, ai, kb, metrics

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(tickets.router, prefix="/tickets", tags=["tickets"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(kb.router, prefix="/kb", tags=["kb"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
