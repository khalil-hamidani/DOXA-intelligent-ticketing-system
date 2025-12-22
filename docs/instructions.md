# DOXA Intelligent Ticketing - Setup & Testing Instructions

This guide explains how to set up and test the DOXA Intelligent Ticketing backend on a new machine (e.g., for a hackathon teammate or judge).

## Prerequisites

Ensure the following are installed on the machine:
1. **Git**: To clone the repository.
2. **Docker Desktop**: Required for the PostgreSQL database.
3. **Python 3.10+**: Required to run the FastAPI backend.

---

## 1. Clone the Repository

Open a terminal (PowerShell or Command Prompt) and run:

```bash
git clone <repository-url>
cd doxa-intelligent-ticketing
```

*(Replace `<repository-url>` with the actual URL of your git repo)*

---

## 2. Backend Setup

1. Navigate to the backend directory:
   ```powershell
   cd backend
   ```

2. Create a Python virtual environment:
   ```powershell
   python -m venv .venv
   ```

3. Activate the virtual environment:
   - **PowerShell**:
     ```powershell
     .\.venv\Scripts\Activate
     ```
   - **Command Prompt (cmd)**:
     ```cmd
     .venv\Scripts\activate.bat
     ```
   - **Bash/Mac/Linux**:
     ```bash
     source .venv/bin/activate
     ```

4. Install required dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

5. Configure Environment Variables:
   - Copy the example environment file to a real `.env` file:
     ```powershell
     # PowerShell
     Copy-Item .env.example .env
     ```
     *(Or manually copy/paste `.env.example` to a new file named `.env`)*
   - The default settings in `.env` are configured to work with the Docker setup below.

---

## 3. Database Setup

1. Ensure **Docker Desktop** is running.

2. Start the PostgreSQL database container:
   - Navigate back to the project root (where `docker-compose.yml` is located):
     ```powershell
     cd ..
     docker-compose up -d db
     ```
   - Wait a few seconds for the database to initialize.

3. Apply Database Migrations (Create Tables):
   - Go back to the `backend` folder:
     ```powershell
     cd backend
     ```
   - Run Alembic to create the database tables:
     ```powershell
     alembic upgrade head
     ```
   - You should see output indicating that revisions are being applied (e.g., `Running upgrade -> 001`).

---

## 4. Start the Backend Server

From the `backend` directory (ensure your virtual environment is still active):

```powershell
uvicorn app.main:app --reload --port 8000
```

You should see output like: `Uvicorn running on http://127.0.0.1:8000`.

---

## 5. Verify Installation

1. **Health Check**:
   - Open your browser to: [http://localhost:8000/health](http://localhost:8000/health)
   - You should see: `{"status":"ok"}`

2. **API Documentation (Swagger UI)**:
   - Open your browser to: [http://localhost:8000/docs](http://localhost:8000/docs)
   - You should see the interactive API documentation page.

3. **Verify Database Tables**:
   - Run this command to list the tables created in the database:
     ```powershell
     docker exec doxa-intelligent-ticketing-db-1 psql -U user -d doxa_db -c "\dt"
     ```
   - You should see a list of tables including `users`, `tickets`, `kb_documents`, etc.

---

## Troubleshooting

- **"Connection refused" error**: Ensure Docker is running and the container is up (`docker ps`).
- **"uvicorn not found"**: Ensure you activated the virtual environment (`.venv`) before running the command.
- **Port 8000 already in use**: Stop the other process or run uvicorn on a different port (e.g., `--port 8001`).
