# AI Module Technical Overview

> **Document Purpose**: Integration guide for Backend Engineers  
> **Last Updated**: December 23, 2025  
> **Status**: PRODUCTION READY

---

## 1️⃣ High-Level Purpose (Plain English)

### What This AI Module Does

The AI module is an **automated ticket processing system** that:

1. **Receives** support tickets from customers
2. **Validates** that tickets are properly formatted and not spam
3. **Classifies** tickets by category (technical, billing, authentication, etc.)
4. **Finds solutions** by searching a knowledge base (KB)
5. **Generates responses** to send to customers
6. **Decides** whether to auto-respond OR escalate to a human agent

### What It Is Responsible For

| Task | Description |
|------|-------------|
| Ticket Validation | Checks if ticket has enough info to process |
| Priority Scoring | Assigns priority score (0-100) based on urgency/impact |
| Category Classification | Tags tickets: `technique`, `facturation`, `authentification`, `autre` |
| KB Search | Retrieves relevant knowledge base articles |
| Response Generation | Creates professional response text |
| Escalation Decision | Decides if human intervention is needed |

### What It Does NOT Do

- ❌ Does NOT store tickets in a persistent database (uses in-memory storage)
- ❌ Does NOT handle user authentication
- ❌ Does NOT manage user accounts
- ❌ Does NOT send actual emails (logs them only)
- ❌ Does NOT integrate with existing backend database

---

## 2️⃣ Folder & File Structure Explained

### Root Level Files

| File | Role | When Used | Called By |
|------|------|-----------|-----------|
| `main.py` | FastAPI server with `/tickets` endpoints | Primary entry point | HTTP requests |
| `ticket_api.py` | Alternative FastAPI server with `/api/v1/tickets` | Alternative entry point | HTTP requests |
| `ticket_orchestrator.py` | Core processing pipeline (8-stage workflow) | Every ticket | Called by API endpoints |
| `models.py` | Data models (Ticket, Feedback) | Always | All components |
| `requirements.txt` | Python dependencies | Installation | pip |

### `/agents/` Folder (Brain of the System)

| File | Role | When Used | Input | Output |
|------|------|-----------|-------|--------|
| `orchestrator.py` | **Main controller** - runs all agents in sequence | Every ticket | Ticket object | Result dict with status |
| `validator.py` | Validates ticket has required fields | Step 1 | Ticket | `{valid: bool, reasons: []}` |
| `scorer.py` | Calculates priority score (0-100) | Step 2 | Ticket | `{score: int, priority: str}` |
| `query_analyzer.py` | Extracts keywords and summarizes issue | Step 3 | Ticket | `{summary, keywords, entities}` |
| `solution_finder.py` | Searches KB for matching solutions | Step 4 | Ticket | `{solution_text, confidence}` |
| `evaluator.py` | Decides if solution is good enough | Step 5 | Ticket | `{confidence, escalate: bool}` |
| `response_composer.py` | Generates response text for customer | Step 6 | Ticket + solution | Response string |
| `feedback_loop.py` | Logs escalated tickets for improvement | On escalation | Ticket | Suggestions list |

### `/kb/` Folder (Knowledge Base)

| File | Role | When Used |
|------|------|-----------|
| `retriever.py` | **ChromaDB retriever** - vector search for KB articles | KB search step |
| `chroma_db/` | Persisted vector database (if exists) | KB search step |
| `texts/`, `pdfs/` | Source documents for KB | Ingestion |

### `/config/` Folder

| File | Role |
|------|------|
| `settings.py` | Environment configuration (API keys, ports) |

---

## 3️⃣ AI Workflow (Step-by-Step)

```
┌──────────────────────────────────────────────────────────────────────┐
│                    TICKET PROCESSING PIPELINE                        │
└──────────────────────────────────────────────────────────────────────┘

    [HTTP Request]
          │
          ▼
    ┌──────────┐
    │ Stage 1  │  CREATE TICKET
    │          │  - Generate unique ID (TKT-XXXXXXXX)
    │          │  - Set status = "pending"
    └────┬─────┘
         │
         ▼
    ┌──────────┐
    │ Stage 2  │  VALIDATE TICKET
    │          │  - Subject >= 5 chars?
    │          │  - Description >= 10 chars?
    │          │  - Valid email?
    │          │  - Not spam?
    └────┬─────┘
         │
    ┌────┴────┐
    │ Valid?  │
    └────┬────┘
         │
    NO ──┴── YES
    │        │
    ▼        ▼
[REJECT]   ┌──────────┐
           │ Stage 3  │  CLASSIFY TICKET
           │          │  - Detect category (technique/facturation/etc)
           │          │  - Adjust priority based on keywords
           └────┬─────┘
                │
                ▼
           ┌──────────┐
           │ Stage 4  │  RETRIEVE KB CONTEXT
           │          │  - Search ChromaDB for matching articles
           │          │  - Get top 5 relevant chunks
           │          │  - Build context string
           └────┬─────┘
                │
                ▼
           ┌──────────┐
           │ Stage 5  │  PROCESS WITH AGENTS
           │          │  - LLM analyzes ticket + KB context
           │          │  - Generates solution
           │          │  - Calculates confidence (0.0 - 1.0)
           └────┬─────┘
                │
                ▼
           ┌──────────┐
           │ Stage 6  │  VALIDATE SOLUTION
           │          │  - Confidence > 0.7 from KB? → SEND
           │          │  - Confidence > 0.85 from agent? → SEND
           │          │  - Confidence 0.5-0.7? → HOLD FOR REVIEW
           │          │  - Confidence < 0.5? → ESCALATE
           └────┬─────┘
                │
         ┌──────┴──────┐
         │             │
    [HIGH CONF]   [LOW CONF]
         │             │
         ▼             ▼
    ┌──────────┐  ┌──────────┐
    │ Stage 7  │  │ Stage 6b │
    │ COMPOSE  │  │ ESCALATE │
    │ RESPONSE │  │          │
    └────┬─────┘  └────┬─────┘
         │             │
         ▼             ▼
    ┌──────────┐  [Notify Human Team]
    │ Stage 9  │  Status = "escalated"
    │ SEND     │
    │ EMAIL    │
    └────┬─────┘
         │
         ▼
    Status = "resolved"
```

---

## 4️⃣ Inputs Required from Backend (CRITICAL)

### Primary Input: Ticket Submission

The AI expects a **POST request** with the following data:

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `subject` | string | ✅ YES | Ticket subject (5-200 chars) | `"Cannot login to my account"` |
| `description` | string | ✅ YES | Detailed description (10-5000 chars) | `"I keep getting error 401..."` |
| `customer_email` | string (email) | ✅ YES | Customer email address | `"user@example.com"` |
| `customer_name` | string | ✅ YES | Customer name (2-100 chars) | `"John Smith"` |
| `priority` | integer | ❌ Optional | Priority 1-5 (default: 3) | `3` |
| `source` | string | ❌ Optional | Where ticket came from | `"api"`, `"email"`, `"portal"` |

### Example Request Body (JSON)

```json
{
  "subject": "Cannot login to my account",
  "description": "I keep getting an error when trying to log in with my correct credentials. Error code 401.",
  "customer_email": "user@example.com",
  "customer_name": "John Smith",
  "priority": 3,
  "source": "api"
}
```

### Secondary Input: Feedback Submission

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ticket_id` | string | ✅ YES | ID of the ticket |
| `satisfied` | boolean | ✅ YES | Was customer satisfied? |
| `reason` | string | ❌ Optional | Additional feedback text |

---

## 5️⃣ Outputs Returned by AI (CRITICAL)

### Immediate Response (After Ticket Submission)

```json
{
  "ticket_id": "TKT-ABC12345",
  "status": "processing",
  "message": "Your ticket has been received and is being processed",
  "estimated_response_time": "Within 2 hours (standard)"
}
```

### Final Ticket State (After Processing)

| Field | Type | Meaning | Backend Usage |
|-------|------|---------|---------------|
| `id` | string | Unique ticket ID | Store as reference |
| `status` | string | Current status (see below) | Display to user |
| `category` | string | Detected category | Use for routing |
| `priority_score` | int (0-100) | Urgency score | Sort/filter tickets |
| `confidence` | float (0.0-1.0) | AI confidence in solution | Quality indicator |
| `solution_text` | string | Generated solution | Display to agent |
| `escalated` | boolean | Was escalated to human? | Assign to agent |
| `escalation_context` | string | Why escalated | Context for agent |
| `final_response` | string | Email-ready response | Send to customer |

### Status Values

| Status | Meaning | What Backend Should Do |
|--------|---------|------------------------|
| `pending` | Just received | Wait |
| `validated` | Passed validation | Wait |
| `processing` | Being analyzed | Wait |
| `resolved` | Solution sent to customer | Mark complete |
| `escalated` | Needs human intervention | Assign to agent |
| `waiting_review` | Solution needs human approval | Show to agent for review |
| `rejected` | Invalid submission | Notify customer to retry |
| `failed` | Processing error | Retry or manual handling |

### Full Response Example (Processed Ticket)

```json
{
  "id": "TKT-ABC12345",
  "status": "resolved",
  "subject": "Cannot login to my account",
  "category": "authentification",
  "priority": 3,
  "priority_score": 65,
  "customer_name": "John Smith",
  "customer_email": "user@example.com",
  "solution": {
    "content": "To reset your password, go to the login page...",
    "confidence": 0.85,
    "source": "kb",
    "kb_references": ["kb_auth_1", "kb_auth_2"]
  },
  "escalated": false,
  "created_at": "2024-12-23T10:30:00",
  "resolved_at": "2024-12-23T10:32:00"
}
```

---

## 6️⃣ Trigger Points (VERY IMPORTANT)

### When AI Should Be Called

| Trigger | Endpoint | Method | Timing |
|---------|----------|--------|--------|
| New ticket created | `/api/v1/tickets` | POST | **Immediately** after customer submits |
| Check ticket status | `/api/v1/tickets/{ticket_id}` | GET | **On-demand** when user checks status |
| Submit feedback | `/tickets/{ticket_id}/feedback` | POST | **After resolution** when customer responds |

### Synchronous vs Asynchronous

| Endpoint | Behavior | What Happens |
|----------|----------|--------------|
| `POST /api/v1/tickets` | **ASYNCHRONOUS** | Returns immediately with `ticket_id`, processes in background |
| `GET /api/v1/tickets/{id}` | **SYNCHRONOUS** | Returns current ticket state immediately |
| `POST /tickets/{id}/feedback` | **SYNCHRONOUS** | Logs feedback and returns immediately |

### Expected Call Flow

```
1. User submits ticket → Backend calls POST /api/v1/tickets
                         ↓
2. AI returns ticket_id immediately (HTTP 202)
                         ↓
3. AI processes in background (takes 1-30 seconds)
                         ↓
4. User/Backend polls GET /api/v1/tickets/{id} to check status
                         ↓
5. When status = "resolved" or "escalated" → processing complete
```

---

## 7️⃣ External Dependencies

### LLM / AI Models

| Dependency | Purpose | Required |
|------------|---------|----------|
| **Mistral AI API** | LLM for validation, scoring, classification | ✅ YES |
| **Sentence Transformers** | Embeddings for KB search (`all-MiniLM-L6-v2`) | ✅ YES |
| **ChromaDB** | Vector database for KB retrieval | ⚠️ Optional (fallback exists) |

### External APIs

| API | Environment Variable | Purpose |
|-----|---------------------|---------|
| Mistral AI | `MISTRAL_API_KEY` or `MISTRALAI_API_KEY` | All LLM operations |
| Tavily (optional) | `TAVILY_API_KEY` | Web search fallback |

### Python Packages (Key Ones)

```
fastapi>=0.100.0
uvicorn>=0.22.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
chromadb>=0.4.0
sentence-transformers>=2.2.0
agno>=0.1.0          # Agent framework
python-dotenv>=1.0.0
```

---

## 8️⃣ Configuration & Environment

### Required Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MISTRAL_API_KEY` | ✅ YES | None | Mistral AI API key |
| `MISTRALAI_API_KEY` | Alternative | None | Alternative key name |
| `MISTRAL_MODEL_ID` | ❌ Optional | `mistral-small-latest` | Which Mistral model to use |
| `API_HOST` | ❌ Optional | `0.0.0.0` | Server host |
| `API_PORT` | ❌ Optional | `7777` | Server port |

### Configuration File

Location: `/ai/config/settings.py`

```python
class Settings(BaseSettings):
    api_host: str = "0.0.0.0"
    api_port: int = 7777
    MISTRAL_API_KEY: str | None = None
    TAVILY_API_KEY: str | None = None
```

### What Happens If Config Is Missing

| Missing Config | Behavior |
|----------------|----------|
| `MISTRAL_API_KEY` missing | ⚠️ **CRITICAL**: Agents will fall back to simple heuristics (much lower quality) |
| ChromaDB not initialized | Uses hardcoded KB entries (4 generic responses) |
| `.env` file missing | Loads from system environment variables |

---

## 9️⃣ Failure Modes & Risks

### What Can Fail

| Failure | Impact | How AI Handles It |
|---------|--------|-------------------|
| Mistral API unavailable | LLM calls fail | Falls back to heuristic rules (lower quality) |
| ChromaDB not found | No KB search | Uses 4 hardcoded KB entries |
| Invalid ticket data | Validation fails | Returns `status: rejected` with reasons |
| LLM returns unparseable response | JSON parsing fails | Uses fallback heuristic |
| Processing timeout | Ticket stuck | Status remains `processing` |

### Safe Fallback Behaviors

1. **Validator fallback**: If LLM fails, uses simple rules (subject/description length)
2. **Scorer fallback**: If LLM fails, uses keyword matching (urgency words)
3. **Solution finder fallback**: If ChromaDB fails, returns generic response
4. **Evaluator**: Always escalates if confidence < 60%

### What Backend Should Expect on Failure

```json
{
  "status": "failed",
  "error": "Error processing ticket",
  "code": 500
}
```

Or for validation failures:

```json
{
  "status": "rejected",
  "reasons": [
    "Subject must be at least 5 characters",
    "Valid customer email required"
  ]
}
```

---

## 🔟 API CONTRACT PROPOSAL (BACKEND-FRIENDLY)

### Endpoint 1: Submit Ticket

```
POST /api/v1/tickets
Content-Type: application/json
```

**Request:**
```json
{
  "subject": "Cannot login to my account",
  "description": "I keep getting an error when trying to log in with my correct credentials",
  "customer_email": "user@example.com",
  "customer_name": "John Smith",
  "priority": 3,
  "source": "api"
}
```

**Response (202 Accepted):**
```json
{
  "ticket_id": "TKT-ABC12345",
  "status": "processing",
  "message": "Your ticket has been received and is being processed",
  "estimated_response_time": "Within 2 hours (standard)"
}
```

---

### Endpoint 2: Get Ticket Status

```
GET /api/v1/tickets/{ticket_id}
```

**Response (200 OK):**
```json
{
  "ticket_id": "TKT-ABC12345",
  "status": "resolved",
  "subject": "Cannot login to my account",
  "customer_name": "John Smith",
  "priority": 3,
  "category": "authentification",
  "created_at": "2024-12-23T10:30:00",
  "resolved_at": "2024-12-23T10:32:00",
  "assigned_to": null,
  "message": "Your issue has been resolved. Check your email for the response."
}
```

---

### Endpoint 3: List Tickets

```
GET /api/v1/tickets?status=resolved&limit=10
```

**Response (200 OK):**
```json
{
  "total": 45,
  "count": 10,
  "skip": 0,
  "limit": 10,
  "tickets": [
    {
      "id": "TKT-ABC12345",
      "status": "resolved",
      "subject": "Cannot login...",
      "customer_name": "John Smith",
      "priority": 3,
      "created_at": "2024-12-23T10:30:00"
    }
  ]
}
```

---

### Endpoint 4: Health Check

```
GET /api/v1/health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "DOXA Ticket Processing API",
  "version": "1.0.0",
  "timestamp": "2024-12-23T10:30:00"
}
```

---

### Endpoint 5: Statistics

```
GET /api/v1/stats
```

**Response (200 OK):**
```json
{
  "total_tickets": 150,
  "resolved": 120,
  "escalated": 25,
  "rejected": 5,
  "resolution_rate": 80.0,
  "average_solution_confidence": 0.78
}
```

---

## 1️⃣1️⃣ Summary for Backend Integration (1 Page MAX)

### ✅ What Endpoint Backend Must Call

| Action | Method | Endpoint |
|--------|--------|----------|
| Submit new ticket | POST | `/api/v1/tickets` |
| Check ticket status | GET | `/api/v1/tickets/{ticket_id}` |
| List all tickets | GET | `/api/v1/tickets` |
| Health check | GET | `/api/v1/health` |

### ✅ What Backend Must Send

```json
{
  "subject": "string (5-200 chars, REQUIRED)",
  "description": "string (10-5000 chars, REQUIRED)",
  "customer_email": "valid email (REQUIRED)",
  "customer_name": "string (2-100 chars, REQUIRED)",
  "priority": "integer 1-5 (OPTIONAL, default 3)",
  "source": "string (OPTIONAL, default 'api')"
}
```

### ✅ What Backend Will Receive

**Immediately after POST:**
- `ticket_id`: Unique ID to track this ticket
- `status`: `"processing"`

**After polling GET:**
- `status`: One of `resolved`, `escalated`, `rejected`, `failed`
- `category`: Detected category
- `message`: Human-readable status message

### ✅ What Backend Must Store

| Data | Purpose |
|------|---------|
| `ticket_id` | Link AI ticket to backend ticket |
| `status` | Display to user |
| `category` | Analytics, routing |
| `confidence` | Quality metrics |
| `escalated` | Assign to human agent |

### ❌ What Backend Must NOT Do

1. **DO NOT** call AI synchronously and block - it processes async
2. **DO NOT** expect emails to actually send (AI logs only)
3. **DO NOT** rely on AI for persistent storage (in-memory only)
4. **DO NOT** call AI without `MISTRAL_API_KEY` configured
5. **DO NOT** expect real-time responses - poll for status

---

## Quick Start Checklist

```
□ Set MISTRAL_API_KEY environment variable
□ Start AI service: uvicorn ticket_api:app --host 0.0.0.0 --port 8000
□ Call POST /api/v1/tickets with ticket data
□ Store returned ticket_id
□ Poll GET /api/v1/tickets/{id} until status != "processing"
□ Handle final status (resolved/escalated/rejected/failed)
```

---

**END OF DOCUMENT**
