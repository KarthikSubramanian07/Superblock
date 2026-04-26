import os

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    def load_dotenv() -> None:
        return None


load_dotenv()

# ASI:One Configuration
ASI_ONE_API_KEY = os.getenv("ASI_ONE_API_KEY", "")
ASI_ONE_ENDPOINT = os.getenv("ASI_ONE_ENDPOINT", "https://api.asi1.ai/v1/chat/completions")
MODEL = os.getenv("ASI_ONE_MODEL", "asi1-mini")

# Agent network configuration
AGENT_ENDPOINT_HOST = os.getenv("AGENT_ENDPOINT_HOST", "127.0.0.1")

AGENT_SEEDS = {
    "ingestion": os.getenv("INGESTION_AGENT_SEED", "superblock-ingestion-seed-la-hacks-2026"),
    "mapping": os.getenv("MAPPING_AGENT_SEED", "superblock-mapping-seed-la-hacks-2026"),
    "diagnosis": os.getenv("DIAGNOSIS_AGENT_SEED", "superblock-diagnosis-seed-la-hacks-2026"),
    "simulation": os.getenv("SIMULATION_AGENT_SEED", "superblock-simulation-seed-la-hacks-2026"),
    "planner": os.getenv("PLANNER_AGENT_SEED", "superblock-planner-seed-la-hacks-2026"),
    "narrator": os.getenv("NARRATOR_AGENT_SEED", "superblock-narrator-seed-la-hacks-2026"),
    "coordinator": os.getenv("COORDINATOR_AGENT_SEED", "superblock-coordinator-seed-la-hacks-2026"),
}

AGENT_PORTS = {
    "ingestion": int(os.getenv("INGESTION_AGENT_PORT", "8101")),
    "mapping": int(os.getenv("MAPPING_AGENT_PORT", "8102")),
    "diagnosis": int(os.getenv("DIAGNOSIS_AGENT_PORT", "8103")),
    "simulation": int(os.getenv("SIMULATION_AGENT_PORT", "8104")),
    "planner": int(os.getenv("PLANNER_AGENT_PORT", "8105")),
    "narrator": int(os.getenv("NARRATOR_AGENT_PORT", "8106")),
    "coordinator": int(os.getenv("COORDINATOR_AGENT_PORT", "8107")),
}


def endpoint_for(agent_key: str) -> str:
    return f"http://{AGENT_ENDPOINT_HOST}:{AGENT_PORTS[agent_key]}/submit"


# Agent-to-agent wiring for true distributed execution
MAPPING_AGENT_ADDRESS = os.getenv("MAPPING_AGENT_ADDRESS", "")
DIAGNOSIS_AGENT_ADDRESS = os.getenv("DIAGNOSIS_AGENT_ADDRESS", "")
SIMULATION_AGENT_ADDRESS = os.getenv("SIMULATION_AGENT_ADDRESS", "")
