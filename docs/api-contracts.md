# API Contracts – DOXA Intelligent Ticketing (Solution 1)

Base URL: /api/v1  
Authentication: JWT Bearer Token  
Content-Type: application/json

---

## Roles

- CLIENT: submits tickets, views own tickets, gives feedback
- AGENT: manages tickets, responds to escalated tickets, views metrics
- ADMIN: manages Knowledge Base, full visibility

---

## Authentication & Profiles

### POST /auth/register
Create an account (CLIENT only).

Request:
```json
{
  "email": "client@example.com",
  "password": "strongpassword"
}
```

Response:
```json
{
  "id": 1,
  "email": "client@example.com",
  "role": "CLIENT"
}
```

---

### POST /auth/login
Authenticate user.

Request:
```json
{
  "email": "client@example.com",
  "password": "strongpassword"
}
```

Response:
```json
{
  "access_token": "jwt.token.here",
  "token_type": "bearer"
}
```

---

### GET /auth/me
Get current user profile.

Response:
```json
{
  "id": 1,
  "email": "client@example.com",
  "role": "CLIENT",
  "language": "en"
}
```

---

## Tickets

### POST /tickets
Submit a ticket (CLIENT).

Request:
```json
{
  "subject": "Login issue",
  "description": "I cannot access my account",
  "category": "TECHNICAL"
}
```

Response:
```json
{
  "id": 12,
  "reference": "REF-2025-0012",
  "status": "OPEN",
  "created_at": "2025-01-01T10:00:00Z"
}
```

---

### GET /tickets
List tickets.

Behavior:
- CLIENT → only own tickets
- AGENT / ADMIN → all tickets

Query params (optional):
- status
- category
- page
- limit

Response:
```json
[
  {
    "id": 12,
    "reference": "REF-2025-0012",
    "subject": "Login issue",
    "status": "AI_ANSWERED",
    "created_at": "2025-01-01T10:00:00Z"
  }
]
```

---

### GET /tickets/{ticket_id}
Get ticket details.

Response:
```json
{
  "id": 12,
  "reference": "REF-2025-0012",
  "subject": "Login issue",
  "description": "I cannot access my account",
  "category": "TECHNICAL",
  "status": "AI_ANSWERED",
  "responses": [
    {
      "source": "AI",
      "content": "Please reset your password.",
      "confidence": 0.82,
      "created_at": "2025-01-01T10:02:00Z"
    }
  ]
}
```

---

### POST /tickets/{ticket_id}/reply
Add a response to a ticket.

Roles:
- AI service
- AGENT

Request:
```json
{
  "source": "AI",
  "content": "Please reset your password.",
  "confidence": 0.82
}
```

---

### PATCH /tickets/{ticket_id}/status
Update ticket status (AGENT / AI).

Request:
```json
{
  "status": "ESCALATED"
}
```

Allowed statuses:
- OPEN
- AI_ANSWERED
- ESCALATED
- CLOSED

---

### POST /tickets/{ticket_id}/feedback
Client feedback after resolution.

Request:
```json
{
  "satisfied": true,
  "comment": "Very fast resolution"
}
```

---

## AI Integration (Backend ↔ AI Team)

### POST /ai/analyze-ticket
Used only by the AI service.test

Request:
```json
{
  "ticket_id": 12,
  "response": "Please reset your password.",
  "confidence": 0.82,
  "kb_sources": [3, 7]
}
```

Response:
```json
{
  "success": true
}
```

---

## Knowledge Base (KB)

### POST /kb/articles
Create a KB article (ADMIN only).

Request:
```json
{
  "title": "Reset Password",
  "category": "AUTH",
  "content": "Steps to reset your password..."
}
```

---

### GET /kb/articles
List KB articles.

---

### GET /kb/articles/{article_id}
Get KB article details.

---

## Metrics & Dashboard

### GET /metrics/overview
Dashboard metrics (AGENT / ADMIN).

Response:
```json
{
  "total_tickets": 120,
  "ai_answered_percentage": 68,
  "escalation_rate": 22,
  "satisfaction_rate": 81
}
```

---

## Notes

- Email ingestion is out of scope
- Attachments are out of scope
- Real-time features are not required
- This API supports Solution 1 only
