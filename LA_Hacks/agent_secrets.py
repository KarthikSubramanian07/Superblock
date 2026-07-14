"""Resolve agent seeds from the environment.

Public git history previously contained fixed seed phrases. Treat any
historically published phrase as compromised: set fresh env vars and
regenerate Agentverse identities.
"""

from __future__ import annotations

import os


def demo_mode_enabled() -> bool:
    return os.getenv("DEMO_MODE", "false").strip().lower() in {"1", "true", "yes", "on"}


def resolve_agent_seed(agent_name: str, *, demo_fallback: str) -> str:
    """
    Prefer AGENT-specific env, then AGENT_SEED, then demo fallback only when DEMO_MODE=true.
    """
    env_key = f"{agent_name.upper()}_AGENT_SEED"
    value = (os.getenv(env_key) or os.getenv("AGENT_SEED") or "").strip()
    if value:
        return value
    if demo_mode_enabled():
        return demo_fallback
    raise SystemExit(
        f"Set {env_key} (or AGENT_SEED). Demo seed fallbacks are disabled when DEMO_MODE=false."
    )
