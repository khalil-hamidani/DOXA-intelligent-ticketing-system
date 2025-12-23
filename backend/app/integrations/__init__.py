"""
Integrations module for DOXA Intelligent Ticketing.

Contains clients for external services (AI, etc.)
"""

from app.integrations.ai_client import (
    ai_client,
    AIClient,
    AIStatus,
    AITicketResponse,
    AI_ENABLED,
)

__all__ = [
    "ai_client",
    "AIClient",
    "AIStatus",
    "AITicketResponse",
    "AI_ENABLED",
]
