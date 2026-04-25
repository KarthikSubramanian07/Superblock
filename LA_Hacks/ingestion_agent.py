"""
ingestion_agent.py
─────────────────────────────────────────────────────────────────────────────
Urban Nervous System — Agent 1: Ingestion
─────────────────────────────────────────────────────────────────────────────
Responsibilities:
  1. Receive raw ALS packets from Apple Watch edge layer
  2. Validate Proof of Human (PoH) via device token
  3. Enforce privacy contract — strip raw biometrics before forwarding
  4. Route validated packets to the Mapping Agent by H3 tile
"""

from uagents import Agent, Context, Protocol
from pydantic import BaseModel, Field
from typing import Optional, Literal

# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────

AGENT_SEEDS = {
    "ingestion":  "ingestion-agent-seed-la-hacks-2026",
    "mapping":    "mapping-agent-seed-la-hacks-2026",
    "diagnosis":  "diagnosis-agent-seed-la-hacks-2026",
    "simulation": "simulation-agent-seed-la-hacks-2026",
    "planner":    "planner-agent-seed-la-hacks-2026",
    "narrator":   "narrator-agent-seed-la-hacks-2026",
}

AGENT_PORTS = {
    "ingestion":  8000,
    "mapping":    8001,
    "diagnosis":  8002,
    "simulation": 8003,
    "planner":    8004,
    "narrator":   8005,
}

# Paste the Mapping Agent address here after running mapping_agent.py first
MAPPING_AGENT_ADDRESS = "agent1q_PASTE_MAPPING_ADDRESS_HERE"

# ─────────────────────────────────────────────────────────────────────────────
# Data Models
# ─────────────────────────────────────────────────────────────────────────────

class ALSPacket(BaseModel):
    """
    The only data that ever leaves the Apple Watch.
    3-field privacy contract + bucketed environmental signals.
    No raw biometrics. No absolute GPS. No audio.
    """
    # Core privacy-layer outputs (Step 1 NPU)
    als_score:        float  = Field(ge=0.0, le=1.0, description="Autonomic Load Score")
    movement_context: Literal["Stationary", "Walking", "Transit"]
    h3_index:         str    = Field(description="H3 Resolution 9 tile (~0.11 km²)")

    # Bucketed environmental signals (never raw dB values)
    noise_bucket:     Literal["Low", "Medium", "High"]
    heat_flag:        bool   = Field(description="Wrist temp delta > 1.5°C from baseline")
    gait_quality:     Literal["Good", "Degraded"]

    # Proof of Human attestation token (Apple DeviceCheck format)
    device_token:     str    = Field(description="PoH-{hex16} attestation token")
    timestamp:        str    = Field(description="ISO 8601 UTC timestamp")


class ValidatedPacket(BaseModel):
    """
    Clean packet forwarded to Mapping Agent.
    Device token is stripped — never leaves the ingestion layer.
    """
    als_score:        float
    movement_context: str
    h3_index:         str
    noise_bucket:     str
    heat_flag:        bool
    gait_quality:     str
    timestamp:        str
    # No device_token field — privacy contract enforced


class IngestionRequest(BaseModel):
    """Wrapper for incoming raw data packets."""
    raw_data: dict = Field(description="Raw ALS packet from edge device")


class IngestionResponse(BaseModel):
    """Response sent back to the originating device."""
    accepted:         bool
    reason:           str
    confidence_score: float


# ─────────────────────────────────────────────────────────────────────────────
# Agent & Protocol
# ─────────────────────────────────────────────────────────────────────────────

ingestion_agent = Agent(
    name="ingestion_agent",
    seed=AGENT_SEEDS["ingestion"],
    port=AGENT_PORTS["ingestion"],
    endpoint=[f"http://127.0.0.1:{AGENT_PORTS['ingestion']}/submit"],
)

ingestion_proto = Protocol("ingestion")


# ─────────────────────────────────────────────────────────────────────────────
# Validation Logic
# ─────────────────────────────────────────────────────────────────────────────

def validate_proof_of_human(packet: ALSPacket) -> tuple[bool, str, float]:
    """
    Validates the device attestation token.
    Returns (is_valid, reason, confidence_score).

    Token format: PoH-{16 hex chars}
    BOT- prefix or wrong length → rejected.
    """
    token = packet.device_token

    if not token.startswith("PoH-"):
        return False, f"Invalid token prefix: {token[:4]}", 0.0

    if len(token) != 20:
        return False, f"Malformed token length: {len(token)} (expected 20)", 0.0

    hex_part = token[4:]
    if not all(c in "0123456789abcdefABCDEF" for c in hex_part):
        return False, "Token contains non-hex characters", 0.0

    # Sanity check: ALS suspiciously perfect values suggest synthetic data
    if packet.als_score in (0.0, 1.0):
        return False, f"Suspicious ALS score: {packet.als_score}", 0.1

    return True, "Valid", 0.95


def strip_device_token(packet: ALSPacket) -> ValidatedPacket:
    """
    Remove the device token before forwarding.
    Privacy contract: token never reaches the Mapping Agent or cloud.
    """
    return ValidatedPacket(
        als_score=        packet.als_score,
        movement_context= packet.movement_context,
        h3_index=         packet.h3_index,
        noise_bucket=     packet.noise_bucket,
        heat_flag=        packet.heat_flag,
        gait_quality=     packet.gait_quality,
        timestamp=        packet.timestamp,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Message Handler
# ─────────────────────────────────────────────────────────────────────────────

@ingestion_proto.on_message(model=IngestionRequest, replies=IngestionResponse)
async def handle_ingestion(ctx: Context, sender: str, msg: IngestionRequest):
    ctx.logger.info(f"📥 Packet received from {sender[:20]}...")

    # Step 1 — Parse raw data into typed ALSPacket
    try:
        packet = ALSPacket(**msg.raw_data)
    except Exception as e:
        ctx.logger.error(f"❌ Parse error: {e}")
        await ctx.send(sender, IngestionResponse(
            accepted=False,
            reason=f"Malformed packet: {e}",
            confidence_score=0.0,
        ))
        return

    # Step 2 — Validate Proof of Human
    is_valid, reason, confidence = validate_proof_of_human(packet)

    if not is_valid:
        ctx.logger.warning(
            f"🚫 Rejected | Token: {packet.device_token} | "
            f"Reason: {reason} | Tile: {packet.h3_index[:10]}..."
        )
        await ctx.send(sender, IngestionResponse(
            accepted=False,
            reason=reason,
            confidence_score=confidence,
        ))
        return

    # Step 3 — Strip device token (privacy contract)
    clean_packet = strip_device_token(packet)

    ctx.logger.info(
        f"✅ Validated | ALS={clean_packet.als_score:.3f} | "
        f"{clean_packet.movement_context} | "
        f"Noise={clean_packet.noise_bucket} | "
        f"Heat={'🌡' if clean_packet.heat_flag else '–'} | "
        f"Gait={clean_packet.gait_quality} | "
        f"Tile={clean_packet.h3_index[:12]}..."
    )

    # Step 4 — Route to Mapping Agent
    if MAPPING_AGENT_ADDRESS != "agent1q_PASTE_MAPPING_ADDRESS_HERE":
        await ctx.send(MAPPING_AGENT_ADDRESS, clean_packet)
        ctx.logger.info(f"📤 Forwarded to Mapping Agent → {MAPPING_AGENT_ADDRESS[:20]}...")
    else:
        ctx.logger.warning(
            "⚠️  MAPPING_AGENT_ADDRESS not set — packet validated but not forwarded. "
            "Paste the Mapping Agent address into ingestion_agent.py."
        )

    # Step 5 — Acknowledge back to sender
    await ctx.send(sender, IngestionResponse(
        accepted=True,
        reason="Validated and forwarded to mapping layer",
        confidence_score=confidence,
    ))


# ─────────────────────────────────────────────────────────────────────────────
# Startup
# ─────────────────────────────────────────────────────────────────────────────

@ingestion_agent.on_event("startup")
async def on_startup(ctx: Context):
    ctx.logger.info("━" * 55)
    ctx.logger.info("🚀 Urban Nervous System — Ingestion Agent")
    ctx.logger.info(f"📍 Address : {ingestion_agent.address}")
    ctx.logger.info(f"🔌 Port    : {AGENT_PORTS['ingestion']}")
    ctx.logger.info(f"🗺  Mapping : {MAPPING_AGENT_ADDRESS[:30]}...")
    ctx.logger.info("✅ Proof-of-Human validation active")
    ctx.logger.info("🔒 Privacy contract enforced (token stripped on forward)")
    ctx.logger.info("⏳ Waiting for ALS packets...")
    ctx.logger.info("━" * 55)


# ─────────────────────────────────────────────────────────────────────────────
# Register & Run
# ─────────────────────────────────────────────────────────────────────────────

ingestion_agent.include(ingestion_proto, publish_manifest=True)

if __name__ == "__main__":
    ingestion_agent.run()