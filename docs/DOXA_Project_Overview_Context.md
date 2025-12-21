# DOXA – Project Overview & Context  
## Solution 1: Intelligent Ticketing System with AI

This document provides a **complete, high-level overview of the project**.  
It is intended for **AI agents, developers, and automation tools** to quickly understand the **context, goals, scope, and constraints** of the project.

---

## 1. Project Context

DOXA is a company facing **increasing customer support demand**, leading to:
- Long response times
- Inconsistent answers
- Overloaded human agents

The goal of this project is to design and implement an **AI-assisted ticketing system** that:
- Automates responses to simple requests
- Escalates complex cases to human agents
- Improves response consistency
- Provides operational visibility through metrics

---

## 2. Chosen Solution

**Solution 1 – Intelligent Ticketing System with AI**

Key characteristics:
- Asynchronous ticket-based support (not real-time calls)
- AI used as a first-level support agent
- Human agents intervene only when necessary
- Centralized Knowledge Base used by both AI and agents

This solution was chosen because it is:
- Feasible within 48 hours
- Scalable and realistic
- Easy to demonstrate to a jury

---

## 3. System Actors & Roles

### Client
- Submits support tickets
- Views ticket status and responses
- Provides satisfaction feedback

### Agent
- Manages escalated tickets
- Responds manually when AI confidence is low
- Views dashboards and metrics

### Admin
- Manages the Knowledge Base
- Has global visibility over the system

### AI Service
- Analyzes incoming tickets
- Generates responses
- Assigns confidence scores
- Suggests ticket categories
- Decides whether to escalate

---

## 4. Functional Scope (What the System Must Do)

### Authentication & Access Control
- Secure login using JWT
- Role-based access (CLIENT / AGENT / ADMIN)

### Ticket Lifecycle
1. Client submits a ticket
2. Ticket is analyzed by AI
3. AI responds automatically OR escalates
4. Human agent resolves escalated tickets
5. Client provides feedback

### AI Assistance
- AI generates responses based on Knowledge Base
- AI returns a confidence score
- Low-confidence responses trigger escalation

### Knowledge Base
- Centralized repository of support articles
- Used by AI for response generation
- Managed by Admin users only

### Metrics & Dashboard
- Total tickets
- Percentage handled by AI
- Escalation rate
- Customer satisfaction rate

---

## 5. Explicitly Out of Scope

The following are **not required** for this project:
- Real-time call handling
- Chatbots or live chat
- Microservices architecture
- Email ingestion (bonus only)
- Attachments (bonus only)

---

## 6. Backend Responsibilities (Critical for AI Agents)

The backend:
- Exposes REST APIs
- Stores tickets, responses, feedback, and KB articles
- Enforces business rules and roles
- Does NOT implement AI logic

The AI service:
- Consumes backend APIs
- Produces responses and confidence scores
- Sends results back to backend via defined contracts

---

## 7. Data Model Summary

Core entities:
- User
- Ticket
- TicketResponse
- KnowledgeBaseArticle
- TicketFeedback

Relationships:
- One client → many tickets
- One ticket → many responses
- One ticket → one feedback
- Knowledge Base shared globally

---

## 8. Non-Functional Constraints

- Time constraint: **48 hours**
- Team size: **8 people**
- Backend developers: **2**
- AI logic must be decoupled
- System must be demo-ready and stable

---

## 9. Success Criteria

The project is considered successful if:
- Tickets can be created, answered, escalated, and closed
- AI ↔ backend integration works
- Metrics are visible
- Demo runs without failure

---

## 10. Design Philosophy

- Simplicity over complexity
- Working system over theoretical completeness
- Clear separation of concerns
- Explicit trade-offs documented

---

## 11. Key Documents (Authoritative)

AI agents and developers must rely on:
- `/docs/api-contracts.md`
- `/docs/DOXA_Locked_Database_Schema_Solution1.md`
- `/docs/DOXA_Backend_TODO_Checklist.md`
- `/docs/demo-scenario.md`

These documents define the **source of truth**.

---

**Status:** ✅ FINAL PROJECT OVERVIEW – READY FOR AI CONTEXT INGESTION
