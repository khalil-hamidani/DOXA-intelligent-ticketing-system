"""ASGI app entrypoint used by uvicorn: `script_new:app`.

This file builds the Agent via `agents.agno_agent.build_agent()` and exposes
the AgentOS app as the module-level `app` variable so uvicorn can import it.
"""
from pathlib import Path
import sys

# Ensure ai/ is on sys.path when running from repo root
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from agents.agno_agent import build_agent
    from agno.os import AgentOS

    agent = build_agent()
    agent_os = AgentOS(id="agent_os", agents=[agent])
    app = agent_os.get_app()
except Exception as e:
    # If app creation fails, raise so uvicorn shows the error
    raise RuntimeError(f"Failed to build AgentOS app: {e}")
