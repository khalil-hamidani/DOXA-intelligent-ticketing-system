# Demo Scenario – DOXA Intelligent Ticketing System  
## Solution 1: AI-Assisted Ticketing

This document describes the **official demo scenario** to be followed during the jury presentation.  
It is designed to be **clear, short (5–7 minutes), and impactful**, showing both **business value** and **technical strength**.

---

## 🎯 Demo Objective

Demonstrate how DOXA reduces customer support delays by:
- Automating ticket responses with AI
- Escalating complex cases to human agents
- Providing visibility through metrics and dashboards

---

## 🕒 Demo Duration

**Total time:** 5–7 minutes  
**Recommended flow:** Linear, no backtracking

---

## 👥 Demo Roles

- **Client** – Submits a support request
- **AI System** – Analyzes and answers tickets
- **Agent** – Handles escalated tickets
- **Admin** – Manages knowledge base (optional)

---

## 🧩 Pre-Demo Setup (DO THIS BEFORE PRESENTATION)

- Backend running and stable
- Database seeded with:
  - 1 Client account
  - 1 Agent account
  - 1 Admin account
  - 3–5 Knowledge Base articles
- Frontend connected to backend
- Swagger UI accessible as fallback

---

## 🧪 Demo Scenario Steps

### Step 1 — Client Submits a Ticket
**Role:** Client

- Client logs in
- Submits a ticket:
  - Subject: “Login problem”
  - Description: “I cannot access my account”
- System generates:
  - Ticket reference (e.g. `REF-2025-0001`)
  - Status = OPEN

🎯 Value shown: Simple, structured ticket submission

---

### Step 2 — AI Analyzes the Ticket
**Role:** AI (automatic)

- AI analyzes ticket content
- AI proposes a response
- AI assigns a confidence score

**Two possible paths:**
- Confidence ≥ threshold → Auto-response
- Confidence < threshold → Escalation

🎯 Value shown: AI automation & intelligence

---

### Step 3 — AI Auto-Response (Happy Path)
**Role:** AI

- Ticket status changes to `AI_ANSWERED`
- AI response is stored
- Client sees the response instantly

🎯 Value shown: Reduced response time

---

### Step 4 — Escalation to Human Agent
**Role:** Agent

- Ticket status becomes `ESCALATED`
- Agent sees ticket in dashboard
- Agent reads full history + AI suggestion
- Agent replies manually
- Ticket is closed

🎯 Value shown: Human-in-the-loop reliability

---

### Step 5 — Client Feedback
**Role:** Client

- Client marks ticket as:
  - Satisfied / Not satisfied
- Optional comment submitted

🎯 Value shown: Customer satisfaction tracking

---

### Step 6 — Dashboard & Metrics
**Role:** Agent / Admin

- Show dashboard metrics:
  - Total tickets
  - % handled by AI
  - Escalation rate
  - Satisfaction rate

🎯 Value shown: Management visibility & KPIs

---

## 🧠 Optional Bonus Demo (If Time Allows)

- Switch UI language (FR / EN / AR)
- Show Knowledge Base article list
- Mention email or attachment support as future extensions

---

## ❗ Demo Safety Rules

- Never refresh mid-demo
- Do not show logs or raw DB
- Keep demo data clean
- If frontend fails → use Swagger UI

---

## 🏆 Jury-Oriented Closing Statement

> “With this system, DOXA can instantly handle simple requests using AI, while complex issues are escalated to agents — reducing delays, improving consistency, and scaling support efficiently.”

---

**Status:** ✅ FINAL DEMO SCENARIO – READY FOR PRESENTATION
