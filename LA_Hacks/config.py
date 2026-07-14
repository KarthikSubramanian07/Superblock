import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / "backend_service" / ".env.local", override=True)

from agent_secrets import resolve_agent_seed

# ASI:One Configuration
ASI_ONE_API_KEY = os.getenv("ASI_ONE_API_KEY", "")
ASI_ONE_ENDPOINT = "https://api.asi1.ai/v1/chat/completions"
MODEL = "asi1"

# Agent Configuration — production requires env seeds (see SECURITY.md).
AGENT_SEEDS = {
    "ingestion": resolve_agent_seed("ingestion", demo_fallback="demo-ingestion-seed"),
    "mapping": resolve_agent_seed("mapping", demo_fallback="demo-mapping-seed"),
    "diagnosis": resolve_agent_seed("diagnosis", demo_fallback="demo-diagnosis-seed"),
    "simulation": resolve_agent_seed("simulation", demo_fallback="demo-simulation-seed"),
    "planner": resolve_agent_seed("planner", demo_fallback="demo-planner-seed"),
    "narrator": resolve_agent_seed("narrator", demo_fallback="demo-narrator-seed"),
}

AGENT_PORTS = {
    "ingestion": 8001,
    "mapping": 8002,
    "diagnosis": 8003,
    "simulation": 8004,
    "planner": 8005,
    "narrator": 8006
}
