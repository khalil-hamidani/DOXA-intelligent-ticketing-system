from agno_agent import build_agent, build_team_with_agent
from agno.os import AgentOS
import uvicorn


def serve_agent_os_port(agent_os: AgentOS, host: str = "127.0.0.1", port: int = 8000):
    """Run the AgentOS ASGI app with uvicorn and print access URL."""
    try:
        app = agent_os.get_app()
    except Exception as e:
        print("AgentOS app not available:", e)
        return

    url = f"http://{host}:{port}"
    print(f"Serving AgentOS app at {url} — starting uvicorn (CTRL+C to stop)")
    uvicorn.run(app, host=host, port=port)


def main():
    agent = build_agent()
    team = build_team_with_agent(agent)

    try:
        agent_os = AgentOS(id="agent_os", agents=[agent])
        serve_agent_os_port(agent_os)
    except Exception as e:
        print("Failed to create or serve AgentOS app:", e)


if __name__ == "__main__":
    main()
