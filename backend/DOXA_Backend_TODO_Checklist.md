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
- [ ] AI confidence threshold agreed (ex: 0.75)

---

## PHASE 1 — PROJECT BOOTSTRAP

- [ ] Python virtual environment created
- [ ] Dependencies installed (FastAPI, SQLAlchemy, Alembic, Pydantic, JWT)
- [ ] `.env.example` created
- [ ] Environment variables loaded correctly
- [ ] `main.py` created
- [ ] `/health` endpoint available
- [ ] API versioning `/api/v1`
- [ ] CORS enabled
- [ ] Swagger UI accessible

---

## PHASE 2 — DATABASE

### Connection & Base
- [ ] PostgreSQL connection configured
- [ ] SQLAlchemy engine + session
- [ ] Base model initialized

### Models (MATCH LOCKED SCHEMA)
- [ ] User model
- [ ] Ticket model
- [ ] TicketResponse model
- [ ] KBArticle model
- [ ] TicketFeedback model
- [ ] TicketAttachment model (optional)

### Enums
- [ ] UserRole
- [ ] TicketStatus
- [ ] ResponseSource

### Migration
- [ ] Alembic initialized
- [ ] Initial migration generated
- [ ] Migration applied successfully

---

## PHASE 3 — AUTH & SECURITY

- [ ] Password hashing (bcrypt)
- [ ] JWT creation
- [ ] JWT validation dependency
- [ ] Role-based access dependency
- [ ] `POST /auth/register` (CLIENT only)
- [ ] `POST /auth/login`
- [ ] `GET /auth/me`
- [ ] Route protection verified

---

## PHASE 4 — TICKETS CORE

### Ticket Creation
- [ ] `POST /tickets`
- [ ] Ticket reference generation (REF-YYYY-XXXX)
- [ ] Default status = OPEN
- [ ] Client ownership enforced

### Ticket Listing
- [ ] `GET /tickets`
- [ ] CLIENT → own tickets only
- [ ] AGENT/ADMIN → all tickets
- [ ] Pagination
- [ ] Filter by status / category

### Ticket Details
- [ ] `GET /tickets/{id}`
- [ ] Responses included
- [ ] Access control enforced

---

## PHASE 5 — AI INTEGRATION

- [ ] `POST /ai/analyze-ticket`
- [ ] Payload validation
- [ ] AI response stored
- [ ] Confidence score stored
- [ ] Status updated based on threshold
- [ ] Escalation handled correctly

---

## PHASE 6 — RESPONSES & ESCALATION

- [ ] `POST /tickets/{id}/reply`
- [ ] AI vs HUMAN source enforced
- [ ] HUMAN replies only by AGENT
- [ ] Responses immutable
- [ ] `PATCH /tickets/{id}/status`
- [ ] Valid status transitions enforced

---

## PHASE 7 — KNOWLEDGE BASE

- [ ] `POST /kb/articles` (ADMIN only)
- [ ] `GET /kb/articles`
- [ ] Filter by category
- [ ] Search by title
- [ ] `GET /kb/articles/{id}`
- [ ] Access rules enforced

---

## PHASE 8 — FEEDBACK

- [ ] `POST /tickets/{id}/feedback`
- [ ] Ticket must be CLOSED
- [ ] One feedback per ticket
- [ ] Satisfaction stored correctly

---

## PHASE 9 — METRICS & DASHBOARD

- [ ] `GET /metrics/overview`
- [ ] Total tickets computed
- [ ] AI answered percentage
- [ ] Escalation rate
- [ ] Satisfaction rate
- [ ] Queries efficient

---

## PHASE 10 — BONUS (OPTIONAL)

- [ ] User language stored and returned
- [ ] Category auto-filled by AI
- [ ] Profile picture URL supported
- [ ] Attachment table usable
- [ ] Attachment endpoint (if time)

---

## PHASE 11 — DEMO & STABILITY

- [ ] Demo users seeded (client / agent / admin)
- [ ] KB articles seeded
- [ ] Sample tickets created
- [ ] Full lifecycle tested end-to-end
- [ ] Swagger clean
- [ ] Backend runs with one command

---

## FINAL RULE

> A working system beats a complex one.  
> Stop at Phase 9 if time is tight.

**STATUS:** ⛔ LOCKED CHECKLIST – DO NOT MODIFY
