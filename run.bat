@echo off
setlocal

echo ==========================================
echo      DOXA Intelligent Ticketing Runner
echo ==========================================

set "PROJECT_ROOT=%CD%"
set "PYTHON_EXE=python"

REM --- Detect Virtual Environment ---
if exist "%PROJECT_ROOT%\.venv\Scripts\python.exe" (
    echo Found virtual environment: .venv
    set "PYTHON_EXE=%PROJECT_ROOT%\.venv\Scripts\python.exe"
) else (
    if exist "%PROJECT_ROOT%\env\Scripts\python.exe" (
        echo Found virtual environment: env
        set "PYTHON_EXE=%PROJECT_ROOT%\env\Scripts\python.exe"
    ) else (
        if exist "%PROJECT_ROOT%\backend\venv\Scripts\python.exe" (
            echo Found virtual environment: backend\venv
            set "PYTHON_EXE=%PROJECT_ROOT%\backend\venv\Scripts\python.exe"
        )
    )
)

REM --- Update IP Configuration ---
if "%~1"=="" (
    echo No IP address provided. Using current configuration.
    echo Usage: run.bat [YOUR_IP_ADDRESS]
    echo Example: run.bat 192.168.1.50
) else (
    echo Updating IP address to %1...
    "%PYTHON_EXE%" update_ip.py %1
)

echo.
echo Starting Backend Server...
REM Using python -m uvicorn avoids issues with broken uvicorn.exe wrappers
start "DOXA Backend" cmd /k "cd backend && "%PYTHON_EXE%" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo.
echo Starting AI Server...
start "DOXA AI" cmd /k "cd ai && "%PYTHON_EXE%" agentoss_server_v2.py --host 0.0.0.0 --port 7777"

echo.
echo Starting Frontend Server...
start "DOXA Frontend" cmd /k "cd frontend && npm run dev -- --host 0.0.0.0"

echo.
echo ==========================================
echo App is running!
echo Frontend: http://%1:3000 (or localhost:3000)
echo Backend:  http://%1:8000 (or localhost:8000)
echo AI Svc:   http://%1:7777 (or localhost:7777)
echo ==========================================
echo Press any key to exit this launcher (servers will stay open)...
pause >nul
