"""
Bureau orchestrator for the Urban Nervous System.

Runs all 6 agents (Ingestion, Mapping, Diagnosis, Simulation, Planner, Narrator)
in a single process. Each agent registers itself with Agentverse on startup
(mailbox=True, publish_agent_details=True), so addresses become discoverable
in the Almanac.

After the first run, copy each agent's printed `agent1q…` address into
`config.py::AGENT_ADDRESSES` so the inter-agent ctx.send chain can resolve.
"""
from __future__ import annotations

from uagents import Bureau

from config import AGENT_ADDRESSES, GATEWAY_PORT
from ingestion_agent import ingestion_agent
from mapping_agent import mapping_agent
from diagnosis_agent import diagnosis_agent
from simulation_agent import simulation_agent
from planner_agent import planner_agent
from narrator_agent import narrator_agent

AGENTS = {
    "ingestion":  ingestion_agent,
    "mapping":    mapping_agent,
    "diagnosis":  diagnosis_agent,
    "simulation": simulation_agent,
    "planner":    planner_agent,
    "narrator":   narrator_agent,
}


def print_address_table() -> None:
    """Print every agent's address so the user can copy them into config.py."""
    print("\n" + "=" * 72)
    print("AGENT ADDRESSES — paste into config.py::AGENT_ADDRESSES")
    print("=" * 72)
    for role, agent in AGENTS.items():
        print(f'    "{role}":  "{agent.address}",')
    print("=" * 72 + "\n")


BUREAU_PORT = 9000


def build_bureau() -> Bureau:
    bureau = Bureau(port=BUREAU_PORT, endpoint=[f"http://127.0.0.1:{BUREAU_PORT}/submit"])
    for agent in AGENTS.values():
        bureau.add(agent)
    return bureau


if __name__ == "__main__":
    print_address_table()

    missing = [role for role, addr in AGENT_ADDRESSES.items() if not addr]
    if missing:
        print(
            "⚠️  AGENT_ADDRESSES still empty for: "
            + ", ".join(missing)
            + ".\n   First run only registers agents — copy the addresses above "
              "into config.py and restart for the inter-agent ctx.send chain."
        )

    print(f"🛰  Bureau starting. Gateway expected on port {GATEWAY_PORT}.")
    build_bureau().run()
