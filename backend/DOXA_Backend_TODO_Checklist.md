# Backend TODO Checklist  
## DOXA – Solution 1: Intelligent Ticketing System

This checklist is **final** and aligned with:
- Locked database schema
- API contracts
- Tender requirements

Use it to **check items as you work**. Do not add scope mid-hackathon.

---

## PHASE 0 — LOCK & ALIGN (NO CODE)

- [x] Repository structure committed
- [x] `/docs/api-contracts.md` committed
- [x] `/docs/DOXA_Locked_Database_Schema_Solution1.md` committed
- [x] `/docs/DOXA_ERD_Solution1.pdf` committed
- [x] Team agreement: NO schema changes
- [] AI confidence threshold agreed (ex: 0.75)

---

## PHASE 1 — PROJECT BOOTSTRAP

- [x] Python virtual environment created
- [x] Dependencies installed (FastAPI, SQLAlchemy, Alembic, Pydantic, JWT)
- [x] `.env.example` created
- [x] Environment variables loaded correctly
- [x] `main.py` created
- [x] `/health` endpoint available
- [x] API versioning `/api/v1`
- [x] CORS enabled
- [x] Swagger UI accessible

---

## PHASE 2 — DATABASE

### Connection & Base
- [x] PostgreSQL connection configured
- [x] SQLAlchemy engine + session
- [x] Base model initialized

### Models (MATCH LOCKED SCHEMA)
- [x] User model
- [x] Ticket model
- [x] TicketResponse model
- [x] KBArticle model
- [x] TicketFeedback model
- [x] TicketAttachment model (optional)

### Enums
- [x] UserRole
- [x] TicketStatus
- [x] ResponseSource

### Migration
- [x] Alembic initialized
- [x] Initial migration generated
- [x] Migration applied successfully

---

## PHASE 3 — AUTH & SECURITY

- [x] Password hashing (bcrypt)
- [x] JWT creation
- [x] JWT validation dependency
- [x] Role-based access dependency
- [x] `POST /auth/register` (CLIENT only)
- [x] `POST /auth/login`
- [x] `GET /auth/me`
- [x] Route protection verified

---

## PHASE 4 — TICKETS CORE

### Ticket Creation
- [x] `POST /tickets`
- [x] Ticket reference generation (REF-YYYY-XXXX)
- [x] Default status = OPEN
- [x] Client ownership enforced

### Ticket Listing
- [x] `GET /tickets`
- [x] CLIENT → own tickets only
- [x] AGENT/ADMIN → all tickets
- [x] Pagination
- [x] Filter by status / category

### Ticket Details
- [x] `GET /tickets/{id}`
- [x] Responses included
- [x] Access control enforced

---

## PHASE 5 — AI INTEGRATION

- [x] `POST /ai/analyze-ticket`
- [x] Payload validation
- [x] AI response stored
- [x] Confidence score stored
- [x] Status updated based on threshold
- [x] Escalation handled correctly

---

## PHASE 6 — RESPONSES & ESCALATION

- [x] `POST /tickets/{id}/reply`
- [x] AI vs HUMAN source enforced
- [x] HUMAN replies only by AGENT
- [x] Responses immutable
- [x] `PATCH /tickets/{id}/status`
- [x] Valid status transitions enforced

---

## PHASE 7 — KNOWLEDGE BASE

- [x] `POST /kb/articles` (ADMIN only)
- [x] `GET /kb/articles`
- [x] Filter by category
- [x] Search by title
- [x] `GET /kb/articles/{id}`
- [x] Access rules enforced

---

## PHASE 8 — FEEDBACK

- [x] `POST /tickets/{id}/feedback`
- [x] Ticket must be CLOSED
- [x] One feedback per ticket
- [x] Satisfaction stored correctly

---

## PHASE 9 — METRICS & DASHBOARD

- [x] `GET /metrics/overview`
- [x] Total tickets computed
- [x] AI answered percentage
- [x] Escalation rate
- [x] Satisfaction rate
- [x] Queries efficient

---

## PHASE 10 — BONUS (OPTIONAL)

- [] User language stored and returned
- [] Category auto-filled by AI
- [] Profile picture URL supported
- [] Attachment table usable
- [] Attachment endpoint (if time)

---

## PHASE 11 — DEMO & STABILITY

- [x] Demo users seeded (client / agent / admin)
- [x] KB articles seeded
- [x] Sample tickets created
- [x] Full lifecycle tested end-to-end
- [x] Swagger clean
- [x] Backend runs with one command

---

## FINAL RULE

> A working system beats a complex one.  
> Stop at Phase 9 if time is tight.

**STATUS:** ⛔ LOCKED CHECKLIST – DO NOT MODIFY
