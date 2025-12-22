import sys
from pathlib import Path

# Allow running this script directly from the `ai/agents` folder by
# adding the parent `ai/` directory to `sys.path` when __package__ is None.
if __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.orchestrator import process_ticket
from models import Ticket


def run_example():
    # Create a sample ticket that should trigger technical handling and sensitive detection
    ticket = Ticket(
        id="TST-001",
        client_name="Alice Dupont",
        email="alice.dupont@example.com",
        subject="Impossible de se connecter - urgent",
        description=(
            "Depuis hier je ne peux plus me connecter à mon compte, "
            "le message d'erreur est 'auth failed'. C'est urgent car c'est en production. "
            "Mon email est alice.dupont@example.com"
        ),
    )

    # Try to use `agno` team concept if available
    team_info = None
    try:
        import agno

        # best-effort: inspect client/team classes
        attrs = dir(agno)
        team_info = {"available": True, "attrs_sample": attrs[:10]}
        print("agno detected: sample attributes:", attrs[:10])

        # simulate a team identifier (in a real setup you'd create/get a Team via agno client)
        team_id = "support_team"
    except Exception as e:
        print("agno not available or failed to import:", e)
        team_id = "support_team"

    # Call the orchestrator with the team id so find_solution can boost team-specific KB
    result = process_ticket(ticket, team=team_id)

    print("--- PROCESS RESULT ---")
    # Print concise structured output
    print("status:", result.get("status"))
    if result.get("status") == "answered":
        print(result.get("message"))
    else:
        print(result.get("message"))
        if result.get("escalation_context"):
            print("escalation_context:", result.get("escalation_context"))


if __name__ == "__main__":
    run_example()
