from agno.agent import Agent
from agno.models.mistral import MistralChat
from agno.os import AgentOS
from agno.team import Team
from dotenv import load_dotenv, find_dotenv
import os
import asyncio

# Optional tool import
try:
    from agno.tools.tavily import TavilyTools
    _TAVILY_AVAILABLE = True
except Exception:
    _TAVILY_AVAILABLE = False

load_dotenv(find_dotenv())

# Instructions:
# - set MISTRALAI_API_KEY in your .env if you plan to use mistralai-backed models
# - This module creates an Agent, a Team containing the agent, and exposes a demo runner

MODEL_ID = os.environ.get("MISTRAL_MODEL_ID", "mistral-small-latest")
# Ensure API keys from .env are exposed under keys expected by adapters
_mistral_key = os.environ.get("MISTRAL_API_KEY") or os.environ.get("MISTRALAI_API_KEY")
if _mistral_key:
    os.environ["MISTRALAI_API_KEY"] = _mistral_key

_tavily_key = os.environ.get("TAVILY_API_KEY") or os.environ.get("TVLY_API_KEY")
if _tavily_key:
    os.environ["TAVILY_API_KEY"] = _tavily_key

if _mistral_key:
    print("Mistral API key loaded from env (masked):", _mistral_key[:4] + "...")
if _tavily_key:
    print("Tavily API key loaded from env (masked):", _tavily_key[:4] + "...")


def build_agent(name: str = "LinkedIn Info Agent") -> Agent:
    """Create an Agno Agent using the MistralChat model and optional Tavily tools."""
    # create model adapter
    Mistral = MistralChat(id=MODEL_ID, temperature=0.7)

    tools = []
    if _TAVILY_AVAILABLE:
        tools.append(TavilyTools())

    our_agent = Agent(model=Mistral, instructions="You are a helpful assistant", tools=tools, name=name)
    return our_agent


def build_team_with_agent(agent: Agent, team_name: str = "support_team") -> Team:
    """Create an Agno Team that contains the given agent (in-memory)."""
    # Team constructor accepts list of members; we pass the agent
    team = Team(members=[agent], name=team_name, instructions=f"Team handling for {team_name}")
    return team


async def _run_agent_once(agent: Agent, prompt: str):
    """Run the agent once using available async API (arun) with fallback to run-like methods."""
    # Try async run (arun / aprint_response / arun variants)
    if hasattr(agent, "arun"):
        return await agent.arun(prompt)
    if hasattr(agent, "arun"):
        return await agent.arun(prompt)
    # fallback: try aprint_response then arun
    if hasattr(agent, "aprint_response"):
        return await agent.aprint_response(prompt)
    raise RuntimeError("Agent run API not available in this Agno installation")


def run_demo(prompt: str = "Give me a short summary of how to reset a password." ):
    """Build agent+team and run a single prompt. Prints result or helpful error message."""
    agent = build_agent()
    team = build_team_with_agent(agent)

    # AgentOS + app creation (optional)
    try:
        agent_os = AgentOS(id="agent_os", agents=[agent])
        app = agent_os.get_app()
    except Exception:
        agent_os = None
        app = None

    print(f"Built agent: {agent.name}; team: {team.name}")

    try:
        out = asyncio.run(_run_agent_once(agent, prompt))
        print("--- AGENT OUTPUT ---")
        print(out)
    except Exception as e:
        print("Failed to run agent interactively:", e)
        print("If this is due to missing API keys, set required env vars (ex: MISTRALAI_API_KEY) in your .env and retry.")


if __name__ == "__main__":
    run_demo()
