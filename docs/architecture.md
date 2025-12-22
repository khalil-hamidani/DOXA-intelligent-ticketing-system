# DOXA – Locked Database Schema  
## Solution 1: Intelligent Ticketing System with AI (Updated Architecture)

This document defines the **final, locked database schema** for Solution 1,  
updated to support an **AI-ready Knowledge Base architecture (documents, snippets, embeddings)**.

This schema is **authoritative and immutable during the hackathon**.

---

## 1. users

| Column | Type | Constraints / Notes |
|------|------|---------------------|
| id | BIGSERIAL | Primary Key |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| password_hash | TEXT | NOT NULL |
| role | ENUM | CLIENT / AGENT / ADMIN |
| language | VARCHAR(5) | DEFAULT 'en' |
| profile_picture_url | TEXT | NULL (bonus) |
| is_active | BOOLEAN | DEFAULT true |
| created_at | TIMESTAMP | DEFAULT now() |

**Rules**
- Email is unique
- Users are never hard-deleted
- Role checks enforced at application level

---

## 2. tickets

| Column | Type | Constraints / Notes |
|------|------|---------------------|
| id | UUID | Primary Key |
| reference | VARCHAR(20) | UNIQUE (REF-YYYY-XXXX) |
| client_id | BIGINT | FK → users.id |
| assigned_agent_id | BIGINT | FK → users.id, NULL |
| subject | VARCHAR(255) | NOT NULL |
| description | TEXT | NOT NULL |
| category | VARCHAR(100) | Manual or AI |
| status | ENUM | OPEN / AI_ANSWERED / ESCALATED / CLOSED |
| ai_confidence | FLOAT | 0 ≤ value ≤ 1 |
| created_at | TIMESTAMP | DEFAULT now() |
| updated_at | TIMESTAMP | DEFAULT now() |


**Rules**
- One client owns one ticket
- Agent assignment only when escalated
- Status transitions enforced in service layer

---

## 3. ticket_responses

| Column | Type | Constraints / Notes |
|------|------|---------------------|
| id | UUID | Primary Key |
| ticket_id | UUID | FK → tickets.id |
| source | ENUM | AI / HUMAN |
| content | TEXT | NOT NULL |
| confidence | FLOAT | NULL for HUMAN |
| created_at | TIMESTAMP | DEFAULT now() |

**Rules**
- Responses are immutable
- Confidence applies only to AI responses

---

## 4. KB_documents

| Column | Type | Constraints / Notes |
|------|------|---------------------|
| id | UUID | Primary Key |
| title | VARCHAR(255) | NOT NULL |
| content | TEXT | NOT NULL |
| category | VARCHAR(100) | Technical / Billing / etc. |
| embeddings | VECTOR | AI vector representation |
| created_at | TIMESTAMP | DEFAULT now() |
| Champ | Type | Description  |


**Rules**
- KB documents represent the authoritative knowledge base
- Used by AI for retrieval and response generation
- Embeddings are generated asynchronously
- Articles are versionless (hackathon scope)

---

## 5. KB_snippets

| Column | Type | Constraints / Notes |
|------|------|---------------------|
| id | UUID | Primary Key |
| doc_id | UUID | FK → KB_documents.id |
| content | TEXT | NOT NULL |
| relevance_score | FLOAT | AI relevance score |
| Champ | Type | Description  |

**Rules**
- Each snippet belongs to exactly one KB document
- Snippets are optimized chunks for AI retrieval
- Snippets are not edited manually
- Deleting a document deletes its snippets (CASCADE)

---

## 6. KB_updates

| Column | Type | Constraints / Notes |
|------|------|---------------------|
| id | UUID | Primary Key |
| ticket_id | UUID | FK → tickets.id |
| change_type | ENUM | new_doc / enrich / correction |
| content | TEXT | NOT NULL |
| timestamp | TIMESTAMP | DEFAULT now() |
| Champ | Type | Description  |

**Rules**
- Captures KB evolution driven by resolved tickets
- Used for post-processing or offline enrichment
- No direct impact on live KB during hackathon

---

## 7. ticket_feedback

| Column | Type | Constraints / Notes |
|------|------|---------------------|
| id | UUID | Primary Key |
| ticket_id | UUID | UNIQUE, FK → tickets.id |
| satisfied | BOOLEAN | NOT NULL |
| comment | TEXT | NULL |
| created_at | TIMESTAMP | DEFAULT now() |

**Rules**
- One feedback per ticket
- Feedback allowed only when ticket is CLOSED

---

## 8. ticket_attachments (Bonus)

| Column | Type | Constraints / Notes |
|------|------|---------------------|
| id | UUID | Primary Key |
| ticket_id | UUID | FK → tickets.id |
| file_url | TEXT | NOT NULL |
| file_type | VARCHAR(50) | pdf / png / jpg |
| uploaded_at | TIMESTAMP | DEFAULT now() |

**Rules**
- Optional feature
- Table exists even if endpoints are not implemented

---

## ENUM Definitions

```sql
user_role = ('CLIENT', 'AGENT', 'ADMIN')
ticket_status = ('OPEN', 'AI_ANSWERED', 'ESCALATED', 'CLOSED')
response_source = ('AI', 'HUMAN')
kb_update_type = ('new_doc', 'enrich', 'correction')
```

---

## Design Guarantees

- AI-ready KB architecture (documents + snippets + embeddings)
- Referential integrity via foreign keys
- Strict lifecycle control via enums
- Clear separation between operational data and AI knowledge
- Bonus-ready without over-engineering
- Stable and final for 48h hackathon execution

---

**Status:** 🔒 LOCKED – NO CHANGES ALLOWED