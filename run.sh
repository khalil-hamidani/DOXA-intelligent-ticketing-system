#!/bin/bash

echo "=========================================="
echo "     DOXA Intelligent Ticketing Runner"
echo "=========================================="

PROJECT_ROOT=$(pwd)
PYTHON_EXE="python3"

# --- Detect Virtual Environment ---
if [ -f "$PROJECT_ROOT/.venv/bin/python" ]; then
    echo "Found virtual environment: .venv"
    PYTHON_EXE="$PROJECT_ROOT/.venv/bin/python"
elif [ -f "$PROJECT_ROOT/env/bin/python" ]; then
    echo "Found virtual environment: env"
    PYTHON_EXE="$PROJECT_ROOT/env/bin/python"
elif [ -f "$PROJECT_ROOT/backend/venv/bin/python" ]; then
    echo "Found virtual environment: backend/venv"
    PYTHON_EXE="$PROJECT_ROOT/backend/venv/bin/python"
fi

# --- Update IP Configuration ---
if [ -z "$1" ]; then
    echo "No IP address provided. Using current configuration."
    echo "Usage: ./run.sh [YOUR_IP_ADDRESS]"
else
    echo "Updating IP address to $1..."
    "$PYTHON_EXE" update_ip.py "$1"
fi

echo ""
echo "Starting Backend Server..."
# Run backend in background using explicit python path and module execution
(cd backend && "$PYTHON_EXE" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload) &
BACKEND_PID=$!

echo "Starting AI Server..."
# Run AI in background using explicit python path
(cd ai && "$PYTHON_EXE" agentoss_server_v2.py --host 0.0.0.0 --port 7777) &
AI_PID=$!

echo "Starting Frontend Server..."
# Run frontend
(cd frontend && npm run dev -- --host 0.0.0.0) &
FRONTEND_PID=$!

echo ""
echo "=========================================="
echo "App is running!"
echo "Frontend: http://$1:3000 (or localhost:3000)"
echo "Backend:  http://$1:8000 (or localhost:8000)"
echo "AI Svc:   http://$1:7777 (or localhost:7777)"
echo "Press Ctrl+C to stop all servers."
echo "=========================================="

# Handle shutdown
trap "kill $BACKEND_PID $AI_PID $FRONTEND_PID; exit" SIGINT SIGTERM

wait
