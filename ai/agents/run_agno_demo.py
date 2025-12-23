"""
run_agno_demo.py

Demo script to run AgentOS with a single agent and serve the FastAPI ASGI app.
"""

from agno_agent import build_agent, build_team_with_agent
from agno.os import AgentOS
import uvicorn
import logging

# -----------------------------
# Logging
# -----------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# -----------------------------
# Initialize AgentOS app globally
# -----------------------------
our_agent = build_agent()
agent_os = AgentOS(id="agent_os", agents=[our_agent])
app = agent_os.get_app()  # This is the ASGI app FastAPI uses

# -----------------------------
# Function to serve AgentOS
# -----------------------------
def serve_agent_os_port(host: str = "0.0.0.0", port: int = 7777):
    """
    Run the AgentOS ASGI app with uvicorn and print access URL.
    host: 0.0.0.0 binds to all network interfaces
    """
    url = f"http://{host}:{port}"
    print(f"Serving AgentOS app at {url} — starting uvicorn (CTRL+C to stop)")
    
    # Use import string to enable reload
    uvicorn.run("run_agno_demo:app", host=host, port=port, log_level="info", reload=True)


# -----------------------------
# Main function
# -----------------------------
def main():
    try:
        logger.info("✅ AgentOS initialized with agent")
        serve_agent_os_port()
    except Exception as e:
        logger.error(f"Failed to create or serve AgentOS app: {e}")


# -----------------------------
# Run script
# -----------------------------
if __name__ == "__main__":
    main()
