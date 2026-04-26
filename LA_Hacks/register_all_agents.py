import os
from uagents_core.utils.registration import (
    register_chat_agent,
    RegistrationRequestCredentials,
)


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _cred(seed_env: str) -> RegistrationRequestCredentials:
    return RegistrationRequestCredentials(
        agentverse_api_key=_require_env("AGENTVERSE_KEY"),
        agent_seed_phrase=_require_env(seed_env),
    )


def main() -> None:
    # Fixed addresses extracted from local running agents.
    # Coordinator address is optional; set COORDINATOR_AGENT_ADDRESS to include it.
    agents = [
        ("Ingestion", "agent1qv9rls0djufkrp4wsetp0zg75jfh95y40f8484tnvc4d2mftgfvlxmn2760", "INGESTION_AGENT_SEED"),
        ("Mapping", "agent1qf5sexjm6qs0z7kjzg5p68hpgxhcwnk073ar7przgctal2cvfl9dkv465ta", "MAPPING_AGENT_SEED"),
        ("Diagnosis", "agent1qtmwxzxl6ec5w6rkg0uxp7xlw5jukwpyxk0x07djdcvw7g9cy6ulj3h03cp", "DIAGNOSIS_AGENT_SEED"),
        ("Simulation", "agent1qdzfzq4kk2twf36pwu7xtxs6fktut99hsec04gr5ye55a8nd8qc2gjsxw3n", "SIMULATION_AGENT_SEED"),
        ("Planner", "agent1qvzu8hw59wv8h82tzn6mcak86y9hsp8h2yv55l50df2f3dz2jp5j7a3u7kc", "PLANNER_AGENT_SEED"),
        ("Narrator", "agent1q0nm0w3jc0vp80kyfwm8cw09fh5puvs9k09mj0u5vnw8tgwpmth72cmaeu4", "NARRATOR_AGENT_SEED"),
    ]

    coordinator_addr = os.getenv("COORDINATOR_AGENT_ADDRESS", "").strip()
    if coordinator_addr:
        agents.append(("Coordinator", coordinator_addr, "COORDINATOR_AGENT_SEED"))

    for name, address, seed_env in agents:
        register_chat_agent(
            name,
            address,
            active=True,
            credentials=_cred(seed_env),
        )
        print(f"[ok] registered {name} -> {address}")


if __name__ == "__main__":
    main()
