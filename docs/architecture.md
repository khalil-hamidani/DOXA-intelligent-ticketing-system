# DOXA – Locked Database Schema  
## Solution 1: Intelligent Ticketing System with AI

This document defines the **final, locked database schema** for Solution 1.  
It covers all required and bonus functionalities and **must not change during the hackathon**.

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
| id | BIGSERIAL | Primary Key |
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
| id | BIGSERIAL | Primary Key |
| ticket_id | BIGINT | FK → tickets.id |
| source | ENUM | AI / HUMAN |
| content | TEXT | NOT NULL |
| confidence | FLOAT | NULL for HUMAN |
| created_at | TIMESTAMP | DEFAULT now() |

**Rules**
- Responses are immutable
- Confidence applies only to AI responses

---

## 4. kb_articles

| Column | Type | Constraints / Notes |
|------|------|---------------------|
| id | BIGSERIAL | Primary Key |
| title | VARCHAR(255) | NOT NULL |
| category | VARCHAR(100) | NOT NULL |
| content | TEXT | NOT NULL |
| created_by | BIGINT | FK → users.id (ADMIN) |
| created_at | TIMESTAMP | DEFAULT now() |

**Rules**
- Only ADMIN can create or modify articles
- Articles are versionless (hackathon scope)

---

## 5. ticket_feedback

| Column | Type | Constraints / Notes |
|------|------|---------------------|
| id | BIGSERIAL | Primary Key |
| ticket_id | BIGINT | UNIQUE, FK → tickets.id |
| satisfied | BOOLEAN | NOT NULL |
| comment | TEXT | NULL |
| created_at | TIMESTAMP | DEFAULT now() |

**Rules**
- One feedback per ticket
- Feedback allowed only when ticket is CLOSED

---

## 6. ticket_attachments (Bonus)

| Column | Type | Constraints / Notes |
|------|------|---------------------|
| id | BIGSERIAL | Primary Key |
| ticket_id | BIGINT | FK → tickets.id |
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
```

---

## Design Guarantees

- Referential integrity via foreign keys
- Strict lifecycle control via enums
- Bonus-ready without over-engineering
- Stable and final for 48h hackathon execution

---

**Status:** 🔒 LOCKED – NO CHANGES ALLOWED
