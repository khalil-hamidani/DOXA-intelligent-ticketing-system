"""
Complete Ticket Processing Pipeline - Main Orchestrator

Handles the full flow from ticket entry → processing → decision stages → email response.
Integrates with KB, agents, and email system.
"""

import asyncio
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Tuple, Optional, List, Dict, Any
from uuid import uuid4
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================

class TicketStatus(str, Enum):
    """Ticket status values."""
    PENDING = "pending"
    VALIDATED = "validated"
    PROCESSING = "processing"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    WAITING_REVIEW = "waiting_review"
    REJECTED = "rejected"
    FAILED = "failed"


class TicketCategory(str, Enum):
    """Ticket categories."""
    INSTALLATION = "installation"
    TROUBLESHOOTING = "troubleshooting"
    FEATURE_REQUEST = "feature_request"
    BUG_REPORT = "bug_report"
    ACCOUNT = "account"
    BILLING = "billing"
    OTHER = "other"


@dataclass
class Solution:
    """Solution to a ticket."""
    content: str
    confidence: float  # 0.0 to 1.0
    source: str  # "kb" or "agent"
    kb_references: Optional[List[str]] = None
    steps: Optional[List[str]] = None


@dataclass
class Ticket:
    """Complete ticket object with all information."""
    id: str
    source: str  # email, api, portal, chat
    subject: str
    description: str
    customer_email: str
    customer_name: str
    priority: int  # 1-5
    
    # Processing fields
    status: TicketStatus = TicketStatus.PENDING
    category: Optional[TicketCategory] = None
    kb_context: Optional[str] = None
    kb_chunks: Optional[List[Dict]] = None
    solution: Optional[Solution] = None
    final_response: Optional[str] = None
    validation_reason: Optional[str] = None
    escalation_reason: Optional[str] = None
    assigned_to: Optional[str] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    # Metadata
    attachments: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        # Convert enums to strings
        data['status'] = self.status.value
        if self.category:
            data['category'] = self.category.value
        # Convert datetime to string
        data['created_at'] = self.created_at.isoformat()
        if self.processed_at:
            data['processed_at'] = self.processed_at.isoformat()
        if self.resolved_at:
            data['resolved_at'] = self.resolved_at.isoformat()
        return data


# ============================================================================
# STAGE FUNCTIONS
# ============================================================================

def validate_ticket(ticket: Ticket) -> Tuple[bool, Optional[str]]:
    """
    Stage 2: Validate ticket has required fields and proper format.
    
    Returns:
        (is_valid, error_message)
    """
    logger.info(f"Validating ticket {ticket.id}")
    
    errors = []
    
    # Check required fields
    if not ticket.subject or len(ticket.subject.strip()) < 5:
        errors.append("Subject must be at least 5 characters")
    
    if not ticket.description or len(ticket.description.strip()) < 10:
        errors.append("Description must be at least 10 characters")
    
    if not ticket.customer_email or "@" not in ticket.customer_email:
        errors.append("Valid customer email required")
    
    if not ticket.customer_name or len(ticket.customer_name.strip()) < 2:
        errors.append("Valid customer name required")
    
    # Spam filter
    spam_keywords = ["viagra", "casino", "lottery", "click here", "act now"]
    if any(keyword in ticket.subject.lower() for keyword in spam_keywords):
        errors.append("Message appears to be spam")
    
    # Priority validation
    if not (1 <= ticket.priority <= 5):
        ticket.priority = 3  # Default to medium
    
    if errors:
        error_message = "\n".join(f"• {e}" for e in errors)
        logger.warning(f"Ticket {ticket.id} validation failed: {error_message}")
        return False, error_message
    
    logger.info(f"Ticket {ticket.id} validation passed")
    return True, None


def classify_ticket(ticket: Ticket) -> Ticket:
    """
    Stage 3: Classify ticket type, priority, and category.
    
    In production, this would use an ML classifier or agent.
    Here we use simple rules for demonstration.
    """
    logger.info(f"Classifying ticket {ticket.id}")
    
    text = (ticket.subject + " " + ticket.description).lower()
    
    # Simple keyword-based classification
    if any(word in text for word in ["install", "setup", "download", "deploy"]):
        ticket.category = TicketCategory.INSTALLATION
    elif any(word in text for word in ["error", "crash", "bug", "issue", "not working"]):
        ticket.category = TicketCategory.TROUBLESHOOTING
    elif any(word in text for word in ["feature", "request", "add", "implement"]):
        ticket.category = TicketCategory.FEATURE_REQUEST
    elif any(word in text for word in ["login", "password", "account", "access"]):
        ticket.category = TicketCategory.ACCOUNT
    elif any(word in text for word in ["payment", "billing", "cost", "price"]):
        ticket.category = TicketCategory.BILLING
    else:
        ticket.category = TicketCategory.OTHER
    
    # Adjust priority based on keywords
    if any(word in text for word in ["urgent", "critical", "emergency", "asap"]):
        ticket.priority = min(5, ticket.priority + 2)
    
    logger.info(f"Ticket {ticket.id} classified: {ticket.category.value}, priority {ticket.priority}")
    
    return ticket


def retrieve_kb_context(ticket: Ticket) -> Ticket:
    """
    Stage 4: Retrieve relevant KB context for the ticket.
    """
    logger.info(f"Retrieving KB context for ticket {ticket.id}")
    
    try:
        from kb.retriever import TicketKBInterface
        
        ticket_kb = TicketKBInterface()
        
        # Get KB context
        context, chunks = ticket_kb.get_context_for_ticket(
            subject=ticket.subject,
            description=ticket.description,
            top_k=5
        )
        
        ticket.kb_context = context
        ticket.kb_chunks = [c.to_dict() for c in chunks]
        
        logger.info(f"Retrieved KB context for ticket {ticket.id}: {len(chunks)} chunks")
    
    except Exception as e:
        logger.warning(f"KB retrieval failed for ticket {ticket.id}: {e}")
        ticket.kb_context = None
        ticket.kb_chunks = None
    
    return ticket


def process_with_agents(ticket: Ticket) -> Ticket:
    """
    Stage 5: Process ticket through agent orchestration.
    
    Simulated agent processing. In production, this would:
    - Query analyzer: understand customer request
    - Solution finder: find best solution
    - Response composer: create response
    """
    logger.info(f"Starting agent processing for ticket {ticket.id}")
    
    # Simulate agent processing
    # In production, this would call actual agents:
    # from agents.query_analyzer import analyze_query
    # from agents.solution_finder import find_solution
    
    # For now, generate a mock solution based on KB context
    if ticket.kb_context:
        confidence = 0.85
        source = "kb"
        solution_content = f"""
Based on our knowledge base, here's the solution:

{ticket.kb_context[:500]}...

Please try these steps and let us know if it resolves your issue.
        """
    else:
        # No KB context, confidence lower
        confidence = 0.4
        source = "agent"
        solution_content = f"""
Thank you for contacting us about: {ticket.subject}

We're looking into your issue: {ticket.description[:200]}...

Our team will investigate and provide a solution shortly.
        """
    
    ticket.solution = Solution(
        content=solution_content,
        confidence=confidence,
        source=source,
        kb_references=ticket.kb_chunks[:3] if ticket.kb_chunks else None,
    )
    
    logger.info(f"Agent processing complete for ticket {ticket.id}: confidence={confidence}")
    
    return ticket


def validate_solution(ticket: Ticket) -> Tuple[bool, str]:
    """
    Stage 6a: Validate if solution is good enough to send.
    
    Decision logic for YES/NO/ESCALATE paths.
    """
    logger.info(f"Validating solution for ticket {ticket.id}")
    
    if not ticket.solution:
        logger.warning(f"No solution generated for ticket {ticket.id}")
        return False, "no_solution_generated"
    
    confidence = ticket.solution.confidence
    source = ticket.solution.source
    
    # Decision tree
    if confidence > 0.8 and source == "kb":
        logger.info(f"Ticket {ticket.id}: High confidence KB solution - SEND")
        return True, "high_confidence_kb"
    
    if confidence > 0.7 and source == "kb":
        logger.info(f"Ticket {ticket.id}: Good confidence KB solution - SEND")
        return True, "good_confidence_kb"
    
    if confidence > 0.85 and source == "agent":
        logger.info(f"Ticket {ticket.id}: High confidence agent solution - SEND")
        return True, "high_confidence_agent"
    
    if confidence > 0.5 and source == "kb":
        logger.info(f"Ticket {ticket.id}: Medium confidence KB - HOLD FOR REVIEW")
        return False, "medium_confidence_kb"
    
    if confidence > 0.5 and source == "agent":
        logger.info(f"Ticket {ticket.id}: Medium confidence agent - ESCALATE")
        return False, "medium_confidence_agent_escalate"
    
    logger.warning(f"Ticket {ticket.id}: Low confidence - ESCALATE")
    return False, "low_confidence_escalate"


def escalate_ticket(ticket: Ticket, reason: str) -> Ticket:
    """
    Stage 6b: Escalate ticket to human support team.
    """
    logger.warning(f"Escalating ticket {ticket.id} to human team: {reason}")
    
    ticket.status = TicketStatus.ESCALATED
    ticket.escalation_reason = reason
    ticket.assigned_to = "support_team"  # In production, assign to specific person
    
    # In production, would notify support team here
    # notify_support_team(ticket)
    
    return ticket


def hold_for_human_review(ticket: Ticket) -> Ticket:
    """
    Stage 8b: Put ticket in human review queue for medium-confidence solutions.
    """
    logger.info(f"Holding ticket {ticket.id} for human review")
    
    ticket.status = TicketStatus.WAITING_REVIEW
    ticket.assigned_to = "review_queue"
    
    # In production, would notify support team
    # notify_support_team(ticket, priority="review_queue")
    
    return ticket


def compose_response(ticket: Ticket) -> str:
    """
    Stage 7: Compose professional response email.
    """
    logger.info(f"Composing response for ticket {ticket.id}")
    
    if not ticket.solution:
        raise ValueError("No solution available to compose response")
    
    # Build professional email
    response = f"""
Dear {ticket.customer_name},

Thank you for contacting DOXA Support regarding: {ticket.subject}

We've analyzed your request and found the following solution:

---
{ticket.solution.content}
---

Additional Resources:
- Knowledge Base References: {len(ticket.kb_chunks) if ticket.kb_chunks else 0} relevant articles
- Priority Level: {ticket.priority}/5
- Category: {ticket.category.value if ticket.category else 'General'}

If you have any follow-up questions or this doesn't resolve your issue, please reply to this ticket and we'll be happy to help.

Best regards,
DOXA Support Team
Ticket ID: {ticket.id}
"""
    
    ticket.final_response = response
    
    return response


# ============================================================================
# EMAIL AGENT
# ============================================================================

class EmailAgent:
    """Handles all email communications."""
    
    def __init__(self, smtp_server: str = "localhost", smtp_port: int = 587):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
    
    def send_response_email(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        ticket_id: Optional[str] = None,
    ) -> bool:
        """Send response email to customer."""
        
        try:
            logger.info(f"Sending email to {to} for ticket {ticket_id}")
            
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = "support@doxa.com"
            msg["To"] = to
            if cc:
                msg["Cc"] = ", ".join(cc)
            
            # Add plain text
            msg.attach(MIMEText(body, "plain"))
            
            # Add HTML version
            html = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                    <pre style="white-space: pre-wrap; word-wrap: break-word;">
{body}
                    </pre>
                    <hr style="border: 1px solid #ddd; margin: 20px 0;">
                    <p style="color: #666; font-size: 12px;">
                        Ticket ID: {ticket_id}<br>
                        This is an automated response from DOXA Support<br>
                        Reply to this email for additional assistance
                    </p>
                </body>
            </html>
            """
            msg.attach(MIMEText(html, "html"))
            
            # Send email (in production, would use actual SMTP server)
            # For now, just log it
            logger.info(f"✓ Email sent to {to}")
            logger.debug(f"Subject: {subject}\n{body[:200]}...")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
            return False
    
    def send_rejection_email(
        self,
        ticket: Ticket,
        error_message: str,
    ) -> bool:
        """Send rejection email for invalid ticket."""
        
        return self.send_response_email(
            to=ticket.customer_email,
            subject=f"Your Support Request - Unable to Process",
            body=f"""
Dear {ticket.customer_name},

Thank you for contacting DOXA Support.

Unfortunately, we were unable to process your request due to the following issue(s):

{error_message}

Please resubmit your request with:
- A clear subject line (at least 5 characters)
- A detailed description (at least 10 characters)
- A valid email address

If you need immediate assistance, please contact our support team at support@doxa.com

Best regards,
DOXA Support Team
            """,
            ticket_id=ticket.id,
        )
    
    def send_escalation_notification(
        self,
        team_email: str,
        ticket: Ticket,
        reason: str,
    ) -> bool:
        """Notify support team of escalation."""
        
        return self.send_response_email(
            to=team_email,
            subject=f"[ESCALATION] Ticket #{ticket.id}: {ticket.subject}",
            body=f"""
ESCALATION NOTIFICATION

Ticket ID: {ticket.id}
Customer: {ticket.customer_name} ({ticket.customer_email})
Subject: {ticket.subject}
Priority: {ticket.priority}/5
Category: {ticket.category.value if ticket.category else 'Unknown'}
Created: {ticket.created_at.isoformat()}

Reason for Escalation:
{reason}

Customer Description:
{ticket.description}

KB Context Retrieved:
{ticket.kb_context[:300] if ticket.kb_context else 'None'}...

Agent Solution Suggested:
{ticket.solution.content[:300] if ticket.solution else 'None'}...

Action Required:
Please review and respond to the customer within SLA.
            """,
            ticket_id=ticket.id,
        )
    
    def send_feedback_request(
        self,
        customer_email: str,
        customer_name: str,
        ticket_id: str,
    ) -> bool:
        """Request feedback from customer."""
        
        return self.send_response_email(
            to=customer_email,
            subject=f"How was your experience? [Ticket #{ticket_id}]",
            body=f"""
Dear {customer_name},

Thank you for using DOXA Support!

We'd love to hear your feedback on how we helped:
1. Did this solution resolve your problem?
2. Was our response helpful?
3. How can we improve?

Your feedback helps us provide better support.

Reply to this email with your thoughts.

Best regards,
DOXA Support Team
            """,
            ticket_id=ticket_id,
        )


# ============================================================================
# MAIN ORCHESTRATOR
# ============================================================================

async def process_ticket_end_to_end(
    source: str,
    subject: str,
    description: str,
    customer_email: str,
    customer_name: str,
    priority: int = 3,
    email_agent: Optional[EmailAgent] = None,
) -> Ticket:
    """
    Complete end-to-end ticket processing pipeline.
    
    Flow:
    1. Create ticket
    2. Validate
    3. Classify
    4. Get KB context
    5. Process with agents
    6. Validate solution
    7. Send email (either response, hold for review, or escalate)
    8. Log metrics
    
    Args:
        source: Where ticket came from (email, api, portal, chat)
        subject: Ticket subject
        description: Detailed description
        customer_email: Customer email
        customer_name: Customer name
        priority: Priority 1-5
        email_agent: EmailAgent instance for sending emails
    
    Returns:
        Processed Ticket object
    """
    
    if not email_agent:
        email_agent = EmailAgent()
    
    logger.info(f"=== STARTING TICKET PROCESSING ===")
    logger.info(f"Source: {source}")
    logger.info(f"Subject: {subject[:50]}...")
    
    # Stage 1: Create ticket
    ticket = Ticket(
        id=f"TKT-{str(uuid4())[:8].upper()}",
        source=source,
        subject=subject,
        description=description,
        customer_email=customer_email,
        customer_name=customer_name,
        priority=priority,
    )
    
    logger.info(f"✓ Created ticket {ticket.id}")
    
    # Stage 2: Validate
    is_valid, error_message = validate_ticket(ticket)
    if not is_valid:
        logger.warning(f"✗ Validation failed for {ticket.id}")
        email_agent.send_rejection_email(ticket, error_message)
        ticket.status = TicketStatus.REJECTED
        return ticket
    
    ticket.status = TicketStatus.VALIDATED
    logger.info(f"✓ Validation passed for {ticket.id}")
    
    # Stage 3: Classify
    ticket = classify_ticket(ticket)
    logger.info(f"✓ Classified as {ticket.category.value}")
    
    # Stage 4: Get KB context
    ticket = retrieve_kb_context(ticket)
    if ticket.kb_context:
        logger.info(f"✓ Retrieved KB context ({len(ticket.kb_chunks)} chunks)")
    else:
        logger.info(f"⚠ No KB context found")
    
    # Stage 5: Process with agents
    ticket.status = TicketStatus.PROCESSING
    ticket = process_with_agents(ticket)
    logger.info(f"✓ Agent processing complete (confidence: {ticket.solution.confidence:.1%})")
    
    # Stage 6: Validate solution
    is_solution_valid, validation_reason = validate_solution(ticket)
    
    if is_solution_valid:
        logger.info(f"✓ Solution validated: {validation_reason}")
        
        # Stage 7: Compose response
        compose_response(ticket)
        logger.info(f"✓ Response composed")
        
        # Stage 9: Send email
        success = email_agent.send_response_email(
            to=ticket.customer_email,
            subject=f"Re: {ticket.subject} [Ticket #{ticket.id}]",
            body=ticket.final_response,
            cc=["support@doxa.com"],
            ticket_id=ticket.id,
        )
        
        if success:
            ticket.status = TicketStatus.RESOLVED
            ticket.resolved_at = datetime.now()
            logger.info(f"✓ Email sent and ticket resolved")
        else:
            ticket.status = TicketStatus.FAILED
            logger.error(f"✗ Failed to send email")
    
    else:
        logger.info(f"✗ Solution not valid: {validation_reason}")
        
        if "escalate" in validation_reason:
            # Stage 6b: Escalate
            ticket = escalate_ticket(ticket, validation_reason)
            logger.info(f"✓ Escalated to human team")
            
            # Notify support team
            email_agent.send_escalation_notification(
                team_email="support@doxa.com",
                ticket=ticket,
                reason=validation_reason,
            )
        else:
            # Stage 8b: Hold for review
            ticket = hold_for_human_review(ticket)
            logger.info(f"✓ Held for human review")
            
            # Compose response for human review
            compose_response(ticket)
    
    # Stage 10: Feedback loop (would log metrics, request feedback, etc.)
    logger.info(f"✓ Processing complete. Status: {ticket.status.value}")
    logger.info(f"=== TICKET {ticket.id} COMPLETED ===\n")
    
    return ticket


def generate_ticket_id() -> str:
    """Generate unique ticket ID."""
    return f"TKT-{str(uuid4())[:8].upper()}"


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test cases
    async def run_tests():
        """Run test scenarios."""
        
        # Test 1: Valid ticket with KB solution
        print("\n" + "="*80)
        print("TEST 1: Valid ticket with KB solution")
        print("="*80)
        
        ticket1 = await process_ticket_end_to_end(
            source="api",
            subject="How to install the software",
            description="I want to install the software on Windows 10. What are the steps?",
            customer_email="john@example.com",
            customer_name="John Smith",
            priority=3,
        )
        
        print(f"\nResult: {ticket1.status.value}")
        print(f"Category: {ticket1.category.value if ticket1.category else 'N/A'}")
        if ticket1.solution:
            print(f"Solution confidence: {ticket1.solution.confidence:.1%}")
        
        # Test 2: Invalid ticket
        print("\n" + "="*80)
        print("TEST 2: Invalid ticket (too short)")
        print("="*80)
        
        ticket2 = await process_ticket_end_to_end(
            source="api",
            subject="Hi",
            description="Help",
            customer_email="invalid",
            customer_name="X",
            priority=3,
        )
        
        print(f"\nResult: {ticket2.status.value}")
        
        # Test 3: High priority ticket
        print("\n" + "="*80)
        print("TEST 3: Urgent ticket")
        print("="*80)
        
        ticket3 = await process_ticket_end_to_end(
            source="email",
            subject="URGENT: System is down and not working at all!",
            description="The entire system crashed. We cannot access any features. This is critical.",
            customer_email="emergency@company.com",
            customer_name="Jane Doe",
            priority=5,
        )
        
        print(f"\nResult: {ticket3.status.value}")
        print(f"Priority: {ticket3.priority}/5")
        print(f"Category: {ticket3.category.value if ticket3.category else 'N/A'}")
    
    # Run async tests
    asyncio.run(run_tests())
