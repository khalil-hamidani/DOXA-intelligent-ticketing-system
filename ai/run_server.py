#!/usr/bin/env python
"""
Start AgentOS backend server
Usage: python run_server.py [host] [port]
"""

import os
import sys
import subprocess

# Change to ai directory
ai_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(ai_dir)

# Get arguments or use defaults
host = sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0"
port = sys.argv[2] if len(sys.argv) > 2 else "8000"

print(f"📡 Starting AgentOS Backend Server")
print(f"   Host: {host}")
print(f"   Port: {port}")
print(f"   Working Directory: {ai_dir}")

# Start uvicorn
cmd = [sys.executable, "-m", "uvicorn", "main:app", "--reload", f"--host={host}", f"--port={port}"]
subprocess.run(cmd)
