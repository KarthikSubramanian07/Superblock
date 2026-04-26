"""
Central config for the Urban Nervous System multi-agent stack.
All agent files import seeds, ports, and peer addresses from here so the Bureau
runs a single coherent set.
"""
from __future__ import annotations

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ─── ASI:One ────────────────────────────────────────────────────────────────
ASI_ONE_API_KEY = os.getenv(
    "ASI_ONE_API_KEY",
    "sk_f61da147c7b243f1bdc371d4cd5ef46b4d6184d043a243099a82e44c98a027de",
)
ASI_ONE_ENDPOINT = os.getenv(
    "ASI_ONE_ENDPOINT",
    "https://api.asi1.ai/v1/chat/completions",
)
ASI_ONE_MODEL = os.getenv("ASI_ONE_MODEL", "asi1-mini")
MODEL = ASI_ONE_MODEL

# ─── Agent seeds (Agentverse address derivation) ─────────────────────────────
AGENT_SEEDS = {
    "ingestion":  "ingestion-agent-seed-la-hacks-2026",
    "mapping":    "mapping-agent-seed-la-hacks-2026",
    "diagnosis":  "diagnosis-agent-seed-la-hacks-2026",
    "simulation": "simulation-agent-seed-la-hacks-2026",
    "planner":    "planner-agent-seed-la-hacks-2026",
    "narrator":   "narrator-agent-seed-la-hacks-2026",
}

# ─── Agent ports (8000 reserved for the FastAPI gateway → UI) ────────────────
AGENT_PORTS = {
    "ingestion":  8001,
    "mapping":    8002,
    "diagnosis":  8003,
    "simulation": 8004,
    "planner":    8005,
    "narrator":   8006,
}

# ─── Agent addresses ─────────────────────────────────────────────────────────
# Filled in after the first Bureau run prints each agent's `agent1q…` address.
# The Bureau computes addresses deterministically from AGENT_SEEDS, so once
# pasted these stay stable across runs.
AGENT_ADDRESSES = {
    "ingestion":  "agent1qfrjfv625jhfz5n6ur37vr8h0xx9mdhgnu6sfhwr2yksy2hfxgtjqtku9tr",
    "mapping":    "agent1qgnhw5kpwtz3xjd3y8qsj7mcufdpes4mgz2n5l700780vvp8law052j459v",
    "diagnosis":  "agent1q0muzg3k6nkczl849kaw7q62kn095khrpu4hg3nh55vw4vu8knuvkszhl82",
    "simulation": "agent1qd5kx6uulfkdsfee2x20sf397hvlts8xz6fq534zsg3pkyf9vl3z2xqeq6u",
    "planner":    "agent1q0nuqrnterfxycglj2q0tu2s49nr8rad8knff23r0u9ney2ncggmsk07f7v",
    "narrator":   "agent1qg8ej0nznmzqgdj62k5tghezyes0wlrd35sf9p6uy02nunz325s5sme2cl0",
}

GATEWAY_PORT = 8000
