# DOXA – Backend Tech Stack  
## Solution 1: Intelligent Ticketing System with AI

This document defines the **official, locked backend technology stack** for Solution 1.  
It is optimized for **speed, stability, clarity, and hackathon delivery**.

---

## 1. Language & Runtime

- **Python 3.11**
  - Mature ecosystem
  - Fast development
  - Excellent AI & web support

---

## 2. Web Framework

- **FastAPI**
  - High performance (ASGI)
  - Automatic OpenAPI / Swagger documentation
  - Native async support
  - Strong typing with Pydantic

- **Uvicorn**
  - ASGI server
  - Lightweight and reliable

---

## 3. Database & Persistence

- **PostgreSQL**
  - Relational integrity
  - Strong constraints & indexing
  - Perfect fit for ticketing systems

- **SQLAlchemy 2.x**
  - Explicit ORM
  - Declarative models
  - Clean relationship handling

- **Alembic**
  - Database migrations
  - Versioned schema control
  - One initial migration only (schema locked)

---

## 4. Data Validation & Serialization

- **Pydantic v2**
  - Request/response validation
  - Schema enforcement
  - Automatic API docs integration

---

## 5. Authentication & Security

- **JWT (JSON Web Tokens)**
  - Stateless authentication
  - Frontend-friendly
  - Easy role enforcement

- **python-jose**
  - JWT encoding/decoding

- **passlib[bcrypt]**
  - Secure password hashing

---

## 6. Authorization Model

- Role-Based Access Control (RBAC)
  - CLIENT
  - AGENT
  - ADMIN

- Enforced via FastAPI dependencies
- Business rules enforced at service layer

---

## 7. Configuration & Environment

- **python-dotenv**
  - Environment variable management

- `.env` / `.env.example`
  - Database URL
  - JWT secret
  - Token expiration
  - AI confidence threshold

---

## 8. Background & Async Tasks

- **FastAPI BackgroundTasks**
  - Lightweight async execution
  - Used for:
    - AI result persistence
    - Non-blocking operations

> No Celery / RabbitMQ (intentionally excluded)

---

## 9. API Design

- RESTful API
- JSON payloads
- Versioned routes: `/api/v1`
- Clear separation:
  - routers
  - services
  - models
  - schemas

---

## 10. Observability & Debugging

- Built-in logging (Python logging)
- Swagger UI for manual testing
- Simple console logs (hackathon-appropriate)

---

## 11. Containerization

- **Docker**
- **Dockerfile** for backend service
- **docker-compose** for local orchestration

---

## 12. Explicitly Excluded (By Design)

The following are **intentionally NOT used**:

- Microservices
- Kubernetes
- GraphQL
- gRPC
- Kafka / RabbitMQ
- Celery
- Redis
- Serverless functions

Reason: unnecessary complexity for a 48-hour hackathon.

---

## 13. Why This Backend Stack Wins

- Fast to implement
- Easy to understand by jury
- Stable under demo conditions
- Strong typing & validation
- Professional, real-world architecture

---

**Status:** 🔒 LOCKED BACKEND STACK – DO NOT CHANGE
