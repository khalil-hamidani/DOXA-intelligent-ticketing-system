#!/usr/bin/env python3
"""
AgentOS Server Startup Script
Runs on port 7777 for os.agno.com connection
"""

import os
import sys
import subprocess
from pathlib import Path

# Get the script directory
script_dir = Path(__file__).parent.absolute()
os.chdir(script_dir)

# Ensure .env is loaded
env_file = script_dir / ".env"
if env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(env_file)

print("\n" + "="*70)
print("🚀 AGENTOSS STARTUP")
print("="*70)
print(f"📂 Working Directory: {os.getcwd()}")
print(f".env File: {env_file}")
print("="*70 + "\n")

# Start the server
cmd = [
    sys.executable,
    str(script_dir / "agentoss_server.py"),
    "--host", "0.0.0.0",
    "--port", "7777",
]

print(f"▶️  Starting: {' '.join(cmd)}\n")

try:
    subprocess.run(cmd, check=False)
except KeyboardInterrupt:
    print("\n\n✋ Server stopped by user")
    sys.exit(0)
