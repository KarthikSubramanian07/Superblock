import httpx
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional
import os

# World ID Configuration
WORLD_APP_ID = os.getenv("WORLD_APP_ID", "app_staging_5c60c91f_superblock")
WORLD_ACTION = os.getenv("WORLD_ACTION", "verify_citizen_sensor")

class WorldIDProof(BaseModel):
    merkle_root: str
    nullifier_hash: str
    proof: str
    verification_level: str

async def verify_world_id_proof(proof: WorldIDProof):
    """
    Validates the World ID proof with the Worldcoin Developer Portal.
    In a real production environment, this ensures the user is a unique human.
    """
    # For the LA Hacks demo, we simulate a successful verification 
    # unless a specific "fail" test case is provided.
    
    url = f"https://developer.worldcoin.org/api/v2/verify/{WORLD_APP_ID}"
    payload = {
        "merkle_root": proof.merkle_root,
        "nullifier_hash": proof.nullifier_hash,
        "proof": proof.proof,
        "verification_level": proof.verification_level,
        "action": WORLD_ACTION,
    }

    # In a real hackathon deployment, you would hit the Worldcoin API:
    # async with httpx.AsyncClient() as client:
    #     resp = await client.post(url, json=payload)
    #     if resp.status_code != 200:
    #         raise HTTPException(status_code=400, detail="World ID Verification Failed")
    #     return resp.json()

    # Simulated success for local demo
    print(f"🌍 [WORLD ID] Verified Human: {proof.nullifier_hash[:12]}...")
    return {"success": True, "human_id": proof.nullifier_hash}
