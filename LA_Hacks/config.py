import os

# ASI:One Configuration
ASI_ONE_API_KEY = "sk_f61da147c7b243f1bdc371d4cd5ef46b4d6184d043a243099a82e44c98a027de"
ASI_ONE_ENDPOINT = "https://api.asi1.ai/v1/chat/completions"
MODEL = "asi1"

# Agent Configuration
AGENT_SEEDS = {
    "ingestion": "ingestion_agent_seed_phrase",
    "mapping": "mapping_agent_seed_phrase", 
    "diagnosis": "diagnosis_agent_seed_phrase",
    "simulation": "simulation_agent_seed_phrase",
    "planner": "planner_agent_seed_phrase",
    "narrator": "narrator_agent_seed_phrase"
}

AGENT_PORTS = {
    "ingestion": 8001,
    "mapping": 8002,
    "diagnosis": 8003,
    "simulation": 8004,
    "planner": 8005,
    "narrator": 8006
}
