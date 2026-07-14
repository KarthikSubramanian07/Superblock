import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / "backend_service" / ".env.local", override=True)

# ASI:One Configuration
ASI_ONE_API_KEY = os.getenv("ASI_ONE_API_KEY", "")
ASI_ONE_ENDPOINT = "https://api.asi1.ai/v1/chat/completions"
MODEL = "asi1"

# Agent Configuration — override via env in production; defaults are demo-only.
AGENT_SEEDS = {
    "ingestion": os.getenv("INGESTION_AGENT_SEED", "ingestion_agent_seed_phrase"),
    "mapping": os.getenv("MAPPING_AGENT_SEED", "mapping_agent_seed_phrase"),
    "diagnosis": os.getenv("DIAGNOSIS_AGENT_SEED", "diagnosis_agent_seed_phrase"),
    "simulation": os.getenv("SIMULATION_AGENT_SEED", "simulation_agent_seed_phrase"),
    "planner": os.getenv("PLANNER_AGENT_SEED", "planner_agent_seed_phrase"),
    "narrator": os.getenv("NARRATOR_AGENT_SEED", "narrator_agent_seed_phrase"),
}

AGENT_PORTS = {
    "ingestion": 8001,
    "mapping": 8002,
    "diagnosis": 8003,
    "simulation": 8004,
    "planner": 8005,
    "narrator": 8006
}
