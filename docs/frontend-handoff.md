# Frontend Implementation Plan & Handoff Checklist
**Project:** DOXA – Solution 1: Intelligent Ticketing System with AI
**Backend Status:** 100% Complete
**API Base URL:** `/api/v1`

---

## 1. Global Frontend Architecture

### Routing Structure
*   **Public Routes:**
    *   `/login`
    *   `/register` (Client only)
*   **Protected Routes (Requires JWT):**
    *   `/dashboard` (Redirects based on role)
    *   `/profile`
*   **Client Routes (Role: CLIENT):**
    *   `/client/tickets` (List)
    *   `/client/tickets/new` (Create)
    *   `/client/tickets/:id` (Details)
*   **Agent Routes (Role: AGENT):**
    *   `/agent/dashboard` (Metrics + Ticket List)
    *   `/agent/tickets/:id` (Details + Actions)
    *   `/agent/kb` (Read-only KB search)
*   **Admin Routes (Role: ADMIN):**
    *   `/admin/dashboard` (Metrics + Ticket List)
    *   `/admin/kb` (Manage KB)
    *   `/admin/kb/new` (Create KB)

### Global Layout
*   **Sidebar/Navigation:**
    *   Dynamic links based on `user.role`.
    *   User Profile summary (Avatar/Name).
    *   Logout button.
*   **Header:**
    *   Breadcrumbs.
    *   Theme toggle (optional).

### Authentication Flow
1.  **Storage:** Store JWT `access_token` in `localStorage` or `HttpOnly Cookie`.
2.  **Interceptor:** Attach `Authorization: Bearer <token>` to EVERY request to `/api/v1/*`.
3.  **Guard:** Check token existence and `user.role` before rendering protected routes. Redirect to `/login` if missing/expired.

---

## 2. Authentication & User Management

### Login Screen
*   **Path:** `/login`
*   **Components:** Email Input, Password Input, Submit Button.
*   **API:** `POST /api/v1/auth/login`
*   **Payload:** `{ "username": "email", "password": "..." }` (Note: OAuth2 form data format usually, but check specific implementation if JSON is expected. Current backend uses JSON schema `Login`).
*   **Success:** Store token, fetch profile (`GET /auth/me`), redirect to role-specific dashboard.
*   **Error:** Show "Invalid credentials".

### Register Screen
*   **Path:** `/register`
*   **Components:** Email, Password, Confirm Password.
*   **API:** `POST /api/v1/auth/register`
*   **Payload:** `{ "email": "...", "password": "..." }`
*   **Success:** Auto-login or redirect to Login with success message.
*   **Role:** Hardcoded to `CLIENT` by backend.

### User Profile
*   **Path:** `/profile`
*   **API:** `GET /api/v1/auth/me`
*   **Display:** Email, Role, Language, ID.
*   **Actions:** Logout (Clear token, redirect to login).

---

## 3. Client Interface (Role: CLIENT)

### Client Dashboard / Ticket List
*   **Path:** `/client/tickets`
*   **API:** `GET /api/v1/tickets`
*   **Params:** `skip=0`, `limit=10` (Pagination).
*   **UI Components:**
    *   "Create Ticket" button.
    *   Data Table: Reference, Subject, Category, Status, Created At.
    *   Status Badges: `OPEN` (Green), `AI_ANSWERED` (Blue), `ESCALATED` (Orange), `CLOSED` (Gray).
*   **Empty State:** "You haven't created any tickets yet."

### Create Ticket
*   **Path:** `/client/tickets/new`
*   **API:** `POST /api/v1/tickets`
*   **Payload:**
    ```json
    {
      "subject": "...",
      "description": "...",
      "category": "TECHNICAL" // Dropdown: TECHNICAL, BILLING, OTHER
    }
    ```
*   **Success:** Redirect to Ticket Details.

### Ticket Details
*   **Path:** `/client/tickets/:id`
*   **API:** `GET /api/v1/tickets/:id`
*   **Display:**
    *   Header: Reference, Status Badge.
    *   Body: Subject, Description, Category.
    *   **Timeline/Conversation:**
        *   Render `responses` array.
        *   If `source` == `AI`: Show as "AI Assistant".
        *   If `source` == `HUMAN`: Show as "Support Agent".
*   **Actions:**
    *   **Submit Feedback:** ONLY visible if `status` == `CLOSED`.

### Submit Feedback
*   **Trigger:** Button on Ticket Details (when Closed).
*   **API:** `POST /api/v1/tickets/:id/feedback`
*   **Payload:**
    ```json
    {
      "satisfied": true, // Boolean toggle/thumbs up-down
      "comment": "Optional text"
    }
    ```
*   **Validation:** Disable if feedback already submitted (Backend returns 400).

---

## 4. Agent Interface (Role: AGENT)

### Agent Dashboard
*   **Path:** `/agent/dashboard`
*   **Components:**
    *   **Metrics Widgets:** (See Section 7).
    *   **Ticket List:** (See below).

### All Tickets List
*   **API:** `GET /api/v1/tickets`
*   **Filters:**
    *   Status Dropdown (OPEN, AI_ANSWERED, ESCALATED, CLOSED).
    *   Category Dropdown.
*   **UI:** Sortable table by `created_at` (DESC default).

### Ticket Management (Details)
*   **Path:** `/agent/tickets/:id`
*   **API:** `GET /api/v1/tickets/:id`
*   **Display:**
    *   Ticket Metadata (Client ID, Reference).
    *   **AI Confidence Score:** Display `ai_confidence` (0.0 - 1.0) as a progress bar or percentage. Color code (Red < 0.5, Green > 0.8).
    *   **Feedback Section:** Call `GET /api/v1/tickets/:id/feedback`. If 404, hide. If 200, display Satisfaction/Comment.
*   **Actions:**
    1.  **Reply:**
        *   Input: Text Area.
        *   API: `POST /api/v1/tickets/:id/reply`
        *   Payload: `{ "content": "..." }`
    2.  **Escalate:**
        *   Button: "Escalate to Human" (Visible if OPEN or AI_ANSWERED).
        *   API: `POST /api/v1/tickets/:id/escalate`
        *   Payload: `{}` (Empty body).
    3.  **Close:**
        *   Button: "Close Ticket" (Visible if ESCALATED or AI_ANSWERED).
        *   API: `POST /api/v1/tickets/:id/close`
        *   Payload: `{}`.

---

## 5. Admin Interface (Role: ADMIN)

### Knowledge Base Management
*   **Path:** `/admin/kb`
*   **API:** `GET /api/v1/kb/documents`
*   **UI:** List of documents. Search bar (filters by `keyword`).
*   **Columns:** Title, Category, Created At.

### Create KB Document
*   **Path:** `/admin/kb/new`
*   **API:** `POST /api/v1/kb/documents`
*   **Payload:**
    ```json
    {
      "title": "...",
      "content": "...",
      "category": "..."
    }
    ```

### View KB Document
*   **Path:** `/admin/kb/:id`
*   **API:** `GET /api/v1/kb/documents/:id`
*   **Display:** Read-only view of content.

---

## 6. AI Integration Awareness

*   **Status `AI_ANSWERED`:**
    *   This means the AI has automatically replied.
    *   **Client View:** Shows the AI response in the timeline.
    *   **Agent View:** Needs review. Agent can choose to `Escalate` (take over) or `Close` (confirm resolution).
*   **Confidence Score:**
    *   Only visible to AGENT/ADMIN.
    *   Use this to highlight "Low Confidence" tickets that need priority attention.

---

## 7. Metrics & Dashboard

*   **Endpoint:** `GET /api/v1/metrics/overview`
*   **Widgets:**
    1.  **Total Tickets:** Simple Card (Number).
    2.  **AI Resolution Rate:** Donut Chart or % Card (`ai_answered_percentage`).
    3.  **Escalation Rate:** % Card (`escalation_rate`).
    4.  **CSAT (Satisfaction):** Star rating or % (`satisfaction_rate`).
    5.  **Tickets by Category:** Bar Chart or Pie Chart (`tickets_by_category` object).

---

## 8. Edge Cases & Error Handling

*   **401 Unauthorized:** Token expired. Redirect to Login immediately.
*   **403 Forbidden:**
    *   Client trying to access Agent pages -> Show "Access Denied" page.
    *   Agent trying to create KB docs -> Hide "Create" button.
*   **404 Not Found:** Ticket ID invalid. Show "Ticket not found" page with "Back to List" button.
*   **Invalid Transitions:**
    *   Trying to Close an OPEN ticket directly (Backend will reject).
    *   **UI Fix:** Disable the "Close" button unless status is ESCALATED or AI_ANSWERED.
*   **Duplicate Feedback:**
    *   Backend returns 400.
    *   **UI Fix:** Hide the feedback form if feedback already exists.

---

## 9. Final Frontend Checklist

- [ ] **Auth:** Login stores token & redirects correctly.
- [ ] **Auth:** Register creates account and redirects.
- [ ] **Client:** Can create a ticket with Category.
- [ ] **Client:** Can see list of OWN tickets only.
- [ ] **Client:** Can see AI responses in ticket details.
- [ ] **Client:** Can submit feedback ONLY when ticket is Closed.
- [ ] **Agent:** Can see ALL tickets.
- [ ] **Agent:** Can filter tickets by Status.
- [ ] **Agent:** Can see AI Confidence score.
- [ ] **Agent:** Can Reply to a ticket.
- [ ] **Agent:** Can Escalate a ticket (Status updates to ESCALATED).
- [ ] **Agent:** Can Close a ticket (Status updates to CLOSED).
- [ ] **Agent:** Can view Client feedback.
- [ ] **Admin:** Can create Knowledge Base documents.
- [ ] **Admin:** Can search Knowledge Base.
- [ ] **Dashboard:** Metrics API is connected and charts render.
- [ ] **General:** 401 errors trigger logout.
- [ ] **General:** 403 errors show friendly message.
