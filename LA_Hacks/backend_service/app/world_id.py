import logging
import os
from typing import Optional

import httpx
from pydantic import BaseModel

logger = logging.getLogger("superblock.world_id")

WORLD_ID_STAGING_URL = "https://developer.worldcoin.org/api/v1/verify/app_staging_5c60c91f_superblock"


def _demo_mode() -> bool:
    return os.getenv("DEMO_MODE", "false").strip().lower() in {"1", "true", "yes", "on"}


class WorldIDProof(BaseModel):
    merkle_root: Optional[str] = None
    nullifier_hash: Optional[str] = None
    proof: Optional[str] = None
    verification_level: Optional[str] = "orb"
    action: Optional[str] = "verify_citizen_sensor"
    is_mock: bool = False


async def verify_world_id_proof(proof: dict) -> bool:
    """
    Verifies a World ID proof via the Worldcoin Developer Portal.

    Demo mode (DEMO_MODE=true, opt-in for local hackathon / CI):
      allows explicit is_mock proofs only.
    Production default (DEMO_MODE unset or false):
      fail-closed; missing/invalid proofs and API errors reject.
    """
    if not proof:
        return False

    if proof.get("is_mock"):
        if _demo_mode():
            logger.info("World ID demo mock accepted (DEMO_MODE=true)")
            return True
        logger.warning("World ID mock rejected (DEMO_MODE=false)")
        return False

    nullifier = proof.get("nullifier_hash")
    merkle_root = proof.get("merkle_root")
    proof_value = proof.get("proof")
    if not nullifier or not merkle_root or not proof_value:
        return False

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                WORLD_ID_STAGING_URL,
                json={
                    "nullifier_hash": nullifier,
                    "merkle_root": merkle_root,
                    "proof": proof_value,
                    "verification_level": proof.get("verification_level") or "orb",
                    "action": proof.get("action") or "verify_citizen_sensor",
                },
                timeout=10.0,
            )
            if response.status_code == 200:
                logger.info("World ID verification succeeded")
                return True
            logger.warning("World ID verification failed: %s", response.text)
            return False
    except Exception as exc:
        logger.error("World ID verification error: %s", exc)
        return False
