"""
AI Service Client - Isolated Integration Layer

This module handles ALL communication with the AI service.
It NEVER raises unhandled exceptions to the caller.
All failures result in graceful fallback behavior.
"""

import os
import logging
import httpx
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

# Configuration
AI_BASE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:7777")
AI_TIMEOUT_SECONDS = float(os.getenv("AI_TIMEOUT_SECONDS", "30"))
AI_POLL_INTERVAL_SECONDS = float(os.getenv("AI_POLL_INTERVAL_SECONDS", "5"))
AI_MAX_POLL_ATTEMPTS = int(os.getenv("AI_MAX_POLL_ATTEMPTS", "12"))
# Default to TRUE for local development - set to "false" to disable
AI_ENABLED = os.getenv("AI_ENABLED", "true").lower() in ("true", "1", "yes")


class AIStatus(str, Enum):
    """AI service response statuses - mapped to AI server's actual values"""

    PROCESSING = "processing"
    PENDING = "pending"
    PENDING_VALIDATION = "pending_validation"
    VALIDATED = "validated"
    RESOLVED = "resolved"
    ANSWERED = "answered"  # AI uses "answered" instead of "resolved"
    ESCALATED = "escalated"
    WAITING_REVIEW = "waiting_review"
    REJECTED = "rejected"
    INVALID = "invalid"  # AI returns "invalid" for rejected tickets
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class AITicketResponse:
    """Structured response from AI service"""

    success: bool
    ai_ticket_id: Optional[str] = None
    status: AIStatus = AIStatus.UNKNOWN
    solution_text: Optional[str] = None
    confidence: Optional[float] = None
    category: Optional[str] = None
    message: Optional[str] = None
    escalation_reason: Optional[str] = None
    error: Optional[str] = None


class AIClient:
    """
    Isolated AI Service Client

    - Handles all HTTP communication with AI service
    - NEVER raises exceptions to caller
    - Always returns structured AITicketResponse
    - Logs all errors internally
    """

    def __init__(self, base_url: str = None, timeout: float = None):
        self.base_url = base_url or AI_BASE_URL
        self.timeout = timeout or AI_TIMEOUT_SECONDS

    def _get_client(self) -> httpx.Client:
        """Create HTTP client with proper timeouts"""
        return httpx.Client(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout, connect=5.0),
            headers={"Content-Type": "application/json"},
        )

    def submit_ticket(
        self,
        ticket_id: str,
        subject: str,
        description: str,
        category: Optional[str] = None,
        language: str = "en",
        priority: int = 3,
    ) -> AITicketResponse:
        """
        Submit a ticket to the AI service for processing.

        This is a NON-BLOCKING call - AI processes asynchronously.
        Returns immediately with ai_ticket_id for polling.

        Args:
            ticket_id: Backend ticket UUID
            subject: Ticket subject (5-200 chars)
            description: Ticket description (10-5000 chars)
            category: Optional category
            language: Language code (en, fr, ar)
            priority: Priority 1-5 (default 3)

        Returns:
            AITicketResponse with ai_ticket_id on success
        """
        payload = {
            "client_name": "Backend User",  # AI expects client_name
            "email": f"ticket-{ticket_id}@doxa.local",  # AI expects email
            "subject": subject[:200],  # Enforce max length
            "description": description[:5000],
        }

        logger.info(f"[AI Client] Submitting ticket to AI: {subject[:50]}...")

        try:
            with self._get_client() as client:
                response = client.post("/tickets", json=payload)

                if response.status_code in [200, 201, 202]:
                    data = response.json()
                    ai_ticket_id = data.get("ticket_id", "")

                    logger.info(
                        f"[AI Client] Ticket submitted successfully: {ai_ticket_id}"
                    )

                    return AITicketResponse(
                        success=True,
                        ai_ticket_id=ai_ticket_id,
                        status=AIStatus.PROCESSING,
                        message=data.get("message", "Ticket submitted to AI"),
                    )
                else:
                    error_msg = f"AI returned status {response.status_code}"
                    logger.warning(f"[AI Client] {error_msg}")
                    return AITicketResponse(
                        success=False, status=AIStatus.FAILED, error=error_msg
                    )

        except httpx.ConnectError as e:
            logger.error(f"[AI Client] Connection failed: {e}")
            return AITicketResponse(
                success=False, status=AIStatus.FAILED, error="AI service unreachable"
            )
        except httpx.TimeoutException as e:
            logger.error(f"[AI Client] Request timeout: {e}")
            return AITicketResponse(
                success=False, status=AIStatus.FAILED, error="AI service timeout"
            )
        except Exception as e:
            logger.error(f"[AI Client] Unexpected error: {e}")
            return AITicketResponse(
                success=False,
                status=AIStatus.FAILED,
                error=f"Unexpected error: {str(e)}",
            )

    def get_ticket_status(self, ai_ticket_id: str) -> AITicketResponse:
        """
        Poll AI service for ticket status.

        Args:
            ai_ticket_id: The ticket ID returned by submit_ticket

        Returns:
            AITicketResponse with current status and solution if resolved
        """
        if not ai_ticket_id:
            return AITicketResponse(
                success=False, status=AIStatus.FAILED, error="No AI ticket ID provided"
            )

        logger.debug(f"[AI Client] Polling status for: {ai_ticket_id}")

        try:
            with self._get_client() as client:
                response = client.get(f"/tickets/{ai_ticket_id}")

                if response.status_code == 200:
                    data = response.json()

                    # DEBUG: Log the full response
                    logger.info(f"[AI Client] Raw response from AI: {data}")

                    # Parse status - can be at top level or in ticket object
                    raw_status = data.get("status", "unknown").lower()
                    logger.info(f"[AI Client] Raw status: {raw_status}")
                    try:
                        status = AIStatus(raw_status)
                    except ValueError:
                        logger.warning(
                            f"[AI Client] Unknown status value: {raw_status}, mapping to UNKNOWN"
                        )
                        status = AIStatus.UNKNOWN

                    # Extract solution and metadata from various possible locations
                    solution_text = None
                    confidence = None
                    category = None

                    # Get ticket object if present
                    ticket_data = data.get("ticket", {})

                    # The AI may return solution in different structures
                    if "solution" in data and isinstance(data["solution"], dict):
                        solution_text = data["solution"].get("content")
                        confidence = data["solution"].get("confidence")
                    elif "final_response" in data:
                        solution_text = data.get("final_response")
                    elif "message" in data:
                        solution_text = data.get("message")

                    # Also check ticket object for solution_text and response
                    if not solution_text:
                        solution_text = ticket_data.get(
                            "solution_text"
                        ) or ticket_data.get("response")

                    # Try to get confidence from multiple sources
                    if confidence is None:
                        confidence = (
                            data.get("solution_confidence")
                            or data.get("confidence")
                            or ticket_data.get("solution_confidence")
                            or ticket_data.get("confidence")
                        )

                    # Category from ticket or top level
                    category = data.get("category") or ticket_data.get("category")

                    # DEBUG: Log extracted values
                    logger.info(
                        f"[AI Client] Extracted - solution_text: {solution_text[:100] if solution_text else 'None'}, confidence: {confidence}, category: {category}"
                    )

                    logger.info(
                        f"[AI Client] Status for {ai_ticket_id}: {status.value}"
                    )

                    return AITicketResponse(
                        success=True,
                        ai_ticket_id=ai_ticket_id,
                        status=status,
                        solution_text=solution_text,
                        confidence=confidence,
                        category=category,
                        message=data.get("message"),
                        escalation_reason=data.get("escalation_reason")
                        or data.get("assigned_to"),
                    )

                elif response.status_code == 404:
                    logger.warning(f"[AI Client] Ticket not found: {ai_ticket_id}")
                    return AITicketResponse(
                        success=False,
                        ai_ticket_id=ai_ticket_id,
                        status=AIStatus.FAILED,
                        error="AI ticket not found",
                    )
                else:
                    error_msg = f"AI returned status {response.status_code}"
                    logger.warning(f"[AI Client] {error_msg}")
                    return AITicketResponse(
                        success=False,
                        ai_ticket_id=ai_ticket_id,
                        status=AIStatus.FAILED,
                        error=error_msg,
                    )

        except httpx.ConnectError as e:
            logger.error(f"[AI Client] Connection failed: {e}")
            return AITicketResponse(
                success=False,
                ai_ticket_id=ai_ticket_id,
                status=AIStatus.FAILED,
                error="AI service unreachable",
            )
        except httpx.TimeoutException as e:
            logger.error(f"[AI Client] Request timeout: {e}")
            return AITicketResponse(
                success=False,
                ai_ticket_id=ai_ticket_id,
                status=AIStatus.FAILED,
                error="AI service timeout",
            )
        except Exception as e:
            logger.error(f"[AI Client] Unexpected error: {e}")
            return AITicketResponse(
                success=False,
                ai_ticket_id=ai_ticket_id,
                status=AIStatus.FAILED,
                error=f"Unexpected error: {str(e)}",
            )

    def health_check(self) -> bool:
        """
        Check if AI service is reachable.

        Returns:
            True if healthy, False otherwise
        """
        try:
            with self._get_client() as client:
                response = client.get("/api/v1/health", timeout=5.0)
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"[AI Client] Health check failed: {e}")
            return False


# Singleton instance for convenience
ai_client = AIClient()
