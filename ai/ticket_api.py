"""
FastAPI Integration for Ticket Processing Pipeline

Provides REST API endpoints for submitting tickets and checking status.
Integrates with the ticket orchestrator for end-to-end processing.
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from enum import Enum

from ticket_orchestrator import (
    process_ticket_end_to_end,
    EmailAgent,
    TicketStatus,
    Ticket,
)

logger = logging.getLogger(__name__)

# Setup FastAPI
app = FastAPI(
    title="DOXA Ticket Processing API",
    description="Submit and track support tickets with AI-powered resolution",
    version="1.0.0"
)

# Initialize email agent
email_agent = EmailAgent()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class Priority(int, Enum):
    """Priority levels."""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    MINIMAL = 1


class TicketSource(str, Enum):
    """Ticket source."""
    EMAIL = "email"
    API = "api"
    PORTAL = "portal"
    CHAT = "chat"


class SubmitTicketRequest(BaseModel):
    """Request to submit a new ticket."""
    
    subject: str = Field(
        ...,
        min_length=5,
        max_length=200,
        description="Ticket subject (5-200 characters)"
    )
    description: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Detailed description (10-5000 characters)"
    )
    customer_email: EmailStr = Field(
        ...,
        description="Customer email address"
    )
    customer_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Customer name"
    )
    priority: Priority = Field(
        Priority.MEDIUM,
        description="Priority level (1-5)"
    )
    source: TicketSource = Field(
        TicketSource.API,
        description="Where ticket came from"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "subject": "Cannot login to my account",
                "description": "I keep getting an error when trying to log in with my correct credentials",
                "customer_email": "user@example.com",
                "customer_name": "John Smith",
                "priority": 3,
                "source": "api"
            }
        }
    )


class TicketResponseDTO(BaseModel):
    """Response DTO for ticket."""
    
    id: str
    status: str
    subject: str
    category: Optional[str] = None
    priority: int
    customer_name: str
    customer_email: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    kb_context_retrieved: bool
    solution_confidence: Optional[float] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "TKT-ABC12345",
                "status": "resolved",
                "subject": "Cannot login to my account",
                "category": "account",
                "priority": 3,
                "customer_name": "John Smith",
                "customer_email": "user@example.com",
                "created_at": "2024-12-22T10:30:00",
                "resolved_at": "2024-12-22T10:32:00",
                "kb_context_retrieved": True,
                "solution_confidence": 0.85
            }
        }
    )


class SubmitTicketResponse(BaseModel):
    """Response after submitting a ticket."""
    
    ticket_id: str
    status: str
    message: str
    estimated_response_time: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ticket_id": "TKT-ABC12345",
                "status": "processing",
                "message": "Your ticket has been received and is being processed",
                "estimated_response_time": "Immediate (if solution found in KB) or within 2 hours (if escalated)"
            }
        }
    )


class TicketStatusResponse(BaseModel):
    """Response for checking ticket status."""
    
    ticket_id: str
    status: str
    subject: str
    customer_name: str
    priority: int
    category: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None
    assigned_to: Optional[str] = None
    message: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ticket_id": "TKT-ABC12345",
                "status": "resolved",
                "subject": "Cannot login to my account",
                "customer_name": "John Smith",
                "priority": 3,
                "category": "account",
                "created_at": "2024-12-22T10:30:00",
                "resolved_at": "2024-12-22T10:32:00",
                "assigned_to": None,
                "message": "Your issue has been resolved. Check your email for the response."
            }
        }
    )


class ErrorResponse(BaseModel):
    """Error response."""
    
    error: str
    code: str
    timestamp: datetime


# ============================================================================
# DATABASE STORAGE (In-memory for demo, use real DB in production)
# ============================================================================

# Store processed tickets in memory (use database in production)
ticket_storage: Dict[str, Ticket] = {}


def save_ticket(ticket: Ticket) -> None:
    """Save ticket to storage."""
    ticket_storage[ticket.id] = ticket
    logger.info(f"Saved ticket {ticket.id} to storage")


def get_ticket(ticket_id: str) -> Optional[Ticket]:
    """Retrieve ticket from storage."""
    return ticket_storage.get(ticket_id)


# ============================================================================
# BACKGROUND TASK FOR ASYNC PROCESSING
# ============================================================================

async def process_ticket_background(
    request: SubmitTicketRequest,
) -> None:
    """Process ticket asynchronously in background."""
    
    logger.info(f"Processing ticket in background for {request.customer_email}")
    
    try:
        ticket = await process_ticket_end_to_end(
            source=request.source.value,
            subject=request.subject,
            description=request.description,
            customer_email=request.customer_email,
            customer_name=request.customer_name,
            priority=request.priority.value,
            email_agent=email_agent,
        )
        
        # Save result
        save_ticket(ticket)
        
        logger.info(f"Background processing complete for ticket {ticket.id}")
    
    except Exception as e:
        logger.error(f"Error processing ticket in background: {e}")


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.post(
    "/api/v1/tickets",
    response_model=SubmitTicketResponse,
    status_code=202,
    summary="Submit a new support ticket",
    tags=["Tickets"]
)
async def submit_ticket(
    request: SubmitTicketRequest,
    background_tasks: BackgroundTasks,
) -> SubmitTicketResponse:
    """
    Submit a new support ticket.
    
    The ticket will be processed asynchronously through:
    1. Validation
    2. Classification
    3. KB context retrieval
    4. Agent processing
    5. Response generation
    6. Email sending
    
    The customer will receive an email response when processing is complete.
    
    **Response Timing:**
    - **Immediate (< 1 minute)**: If solution found in KB with high confidence
    - **Quick (5-10 minutes)**: If escalated to support team
    - **Standard (1-4 hours)**: If requires further investigation
    
    **Request Example:**
    ```json
    {
        "subject": "Cannot login to my account",
        "description": "I keep getting an error when trying to log in",
        "customer_email": "user@example.com",
        "customer_name": "John Smith",
        "priority": 3,
        "source": "api"
    }
    ```
    """
    
    logger.info(f"Received ticket submission from {request.customer_email}")
    logger.info(f"Subject: {request.subject}")
    
    try:
        # Process ticket in background
        background_tasks.add_task(process_ticket_background, request)
        
        # Determine estimated response time based on priority
        priority_to_time = {
            5: "Immediate response (critical)",
            4: "Within 1 hour (high priority)",
            3: "Within 2 hours (standard)",
            2: "Within 4 hours (low priority)",
            1: "Within 24 hours (minimal)",
        }
        
        estimated_time = priority_to_time.get(request.priority.value, "Within 2 hours")
        
        return SubmitTicketResponse(
            ticket_id="TKT-[PROCESSING]",  # Will be assigned during processing
            status="processing",
            message="Your ticket has been received and is being processed by our AI support system",
            estimated_response_time=estimated_time,
        )
    
    except Exception as e:
        logger.error(f"Error submitting ticket: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error processing ticket submission"
        )


@app.get(
    "/api/v1/tickets/{ticket_id}",
    response_model=TicketStatusResponse,
    summary="Check ticket status",
    tags=["Tickets"]
)
async def get_ticket_status(ticket_id: str) -> TicketStatusResponse:
    """
    Get the status and details of a ticket.
    
    **Status Values:**
    - `pending`: Ticket received, validation in progress
    - `validated`: Passed validation, classification starting
    - `processing`: Being processed by agents
    - `resolved`: Solution sent to customer
    - `escalated`: Escalated to human support
    - `waiting_review`: Waiting for human review before sending
    - `rejected`: Invalid submission
    - `failed`: Processing error
    
    **Example Response:**
    ```json
    {
        "ticket_id": "TKT-ABC12345",
        "status": "resolved",
        "subject": "Cannot login to my account",
        "customer_name": "John Smith",
        "priority": 3,
        "category": "account",
        "created_at": "2024-12-22T10:30:00",
        "resolved_at": "2024-12-22T10:32:00",
        "assigned_to": null,
        "message": "Your issue has been resolved. Check your email for the response."
    }
    ```
    """
    
    logger.info(f"Checking status of ticket {ticket_id}")
    
    ticket = get_ticket(ticket_id)
    
    if not ticket:
        logger.warning(f"Ticket {ticket_id} not found")
        raise HTTPException(
            status_code=404,
            detail=f"Ticket {ticket_id} not found"
        )
    
    # Determine status message
    status_messages = {
        TicketStatus.PENDING: "Your ticket is waiting for validation",
        TicketStatus.VALIDATED: "Your ticket has been validated and is being classified",
        TicketStatus.PROCESSING: "Our AI system is working on your ticket",
        TicketStatus.RESOLVED: "Your issue has been resolved. Check your email for the response.",
        TicketStatus.ESCALATED: "Your ticket has been escalated to our support team",
        TicketStatus.WAITING_REVIEW: "Your ticket is waiting for human review",
        TicketStatus.REJECTED: "Your ticket submission was rejected. Please check the validation errors.",
        TicketStatus.FAILED: "There was an error processing your ticket. Please resubmit.",
    }
    
    message = status_messages.get(ticket.status, "Unknown status")
    
    return TicketStatusResponse(
        ticket_id=ticket.id,
        status=ticket.status.value,
        subject=ticket.subject,
        customer_name=ticket.customer_name,
        priority=ticket.priority,
        category=ticket.category.value if ticket.category else None,
        created_at=ticket.created_at,
        resolved_at=ticket.resolved_at,
        assigned_to=ticket.assigned_to,
        message=message,
    )


@app.get(
    "/api/v1/tickets",
    summary="List all tickets",
    tags=["Tickets"]
)
async def list_tickets(
    status: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
) -> Dict[str, Any]:
    """
    List all tickets with optional filtering by status.
    
    **Query Parameters:**
    - `status`: Filter by status (resolved, escalated, pending, etc.)
    - `limit`: Number of results (default 50, max 100)
    - `skip`: Number to skip for pagination (default 0)
    
    **Example:**
    ```
    GET /api/v1/tickets?status=resolved&limit=10&skip=0
    ```
    """
    
    tickets = list(ticket_storage.values())
    
    # Filter by status if provided
    if status:
        tickets = [t for t in tickets if t.status.value == status]
    
    # Apply pagination
    tickets = tickets[skip:skip + limit]
    
    return {
        "total": len(ticket_storage),
        "count": len(tickets),
        "skip": skip,
        "limit": limit,
        "tickets": [
            {
                "id": t.id,
                "status": t.status.value,
                "subject": t.subject[:50],
                "customer_name": t.customer_name,
                "priority": t.priority,
                "created_at": t.created_at,
            }
            for t in tickets
        ]
    }


@app.get(
    "/api/v1/health",
    summary="Health check",
    tags=["System"]
)
async def health_check() -> Dict[str, str]:
    """
    Check API health and connectivity.
    
    Returns:
    ```json
    {
        "status": "healthy",
        "service": "DOXA Ticket Processing API",
        "version": "1.0.0"
    }
    ```
    """
    
    return {
        "status": "healthy",
        "service": "DOXA Ticket Processing API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
    }


@app.get(
    "/api/v1/stats",
    summary="Get statistics",
    tags=["System"]
)
async def get_stats() -> Dict[str, Any]:
    """Get ticket processing statistics."""
    
    all_tickets = list(ticket_storage.values())
    
    resolved = len([t for t in all_tickets if t.status == TicketStatus.RESOLVED])
    escalated = len([t for t in all_tickets if t.status == TicketStatus.ESCALATED])
    rejected = len([t for t in all_tickets if t.status == TicketStatus.REJECTED])
    
    avg_confidence = 0.0
    if all_tickets:
        confidences = [
            t.solution.confidence
            for t in all_tickets
            if t.solution
        ]
        if confidences:
            avg_confidence = sum(confidences) / len(confidences)
    
    return {
        "total_tickets": len(all_tickets),
        "resolved": resolved,
        "escalated": escalated,
        "rejected": rejected,
        "resolution_rate": round(resolved / len(all_tickets) * 100, 2) if all_tickets else 0,
        "average_solution_confidence": round(avg_confidence, 2),
    }


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    
    return {
        "error": exc.detail,
        "code": exc.status_code,
        "timestamp": datetime.now().isoformat(),
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    
    logger.error(f"Unhandled exception: {exc}")
    
    return {
        "error": "Internal server error",
        "code": 500,
        "timestamp": datetime.now().isoformat(),
    }


# ============================================================================
# STARTUP/SHUTDOWN
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup
    logger.info("DOXA Ticket Processing API started")
    logger.info("Endpoints available at http://localhost:8000/docs")
    yield
    # Shutdown
    logger.info("DOXA Ticket Processing API shutting down")


app = FastAPI(
    title="DOXA Ticket Processing API",
    description="Submit and track support tickets with AI-powered resolution",
    version="1.0.0",
    lifespan=lifespan
)


# ============================================================================
# RUN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
