"""
mapping_agent.py
─────────────────────────────────────────────────────────────────────────────
Urban Nervous System — Agent 2: Mapping
─────────────────────────────────────────────────────────────────────────────
Responsibilities:
  1. Receive validated ALS packets from the Ingestion Agent
  2. Aggregate packets per H3 tile into the live 3D Digital Twin
  3. Track tile-level signal profiles (ALS, movement context, noise, etc.)
  4. Detect Red Zones: tile avg ALS > 0.65 sustained for 5+ minutes
  5. Emit RedZoneAlert to the Diagnosis Agent when threshold is crossed
  6. Clear Red Zones when ALS returns to normal
"""

from uagents import Agent, Context, Protocol
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from datetime import datetime, timezone, timedelta
from collections import defaultdict

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

# Paste Diagnosis Agent address after running diagnosis_agent.py
DIAGNOSIS_AGENT_ADDRESS = "agent1q_PASTE_DIAGNOSIS_ADDRESS_HERE"

# Red Zone thresholds
RED_ZONE_ALS_THRESHOLD   = 0.65   # Tile avg ALS must exceed this
RED_ZONE_DURATION_MIN    = 5.0    # For at least this many minutes
TILE_WINDOW_SIZE         = 30     # Max readings kept per tile (~15 min at 30s cadence)

# ─────────────────────────────────────────────────────────────────────────────
# Data Models
# ─────────────────────────────────────────────────────────────────────────────

class ValidatedPacket(BaseModel):
    """
    Received from Ingestion Agent.
    Device token already stripped — privacy contract enforced upstream.
    """
    als_score:        float
    movement_context: Literal["Stationary", "Walking", "Transit"]
    h3_index:         str
    noise_bucket:     Literal["Low", "Medium", "High"]
    heat_flag:        bool
    gait_quality:     Literal["Good", "Degraded"]
    timestamp:        str


class RedZoneAlert(BaseModel):
    """Forwarded to Diagnosis Agent when a tile crosses the Red Zone threshold."""
    h3_index:             str
    avg_als:              float
    sample_count:         int
    context_distribution: dict   # {"Stationary": 0.8, "Walking": 0.15, "Transit": 0.05}
    noise_bucket:         str    # Most common bucket in tile window
    heat_flag:            bool   # True if > 50% of devices flagged heat
    gait_quality:         str    # Most common quality in tile window
    duration_minutes:     float  # How long tile has been in Red Zone


class TileSnapshot(BaseModel):
    """Summary of a single H3 tile — used for dashboard/debug output."""
    h3_index:    str
    avg_als:     float
    sample_count: int
    is_red_zone: bool
    context_distribution: dict
    noise_bucket: str
    heat_flag:   bool
    gait_quality: str


class DigitalTwinSummary(BaseModel):
    """Full Digital Twin state — returned for debug queries."""
    active_tiles:  int
    red_zone_count: int
    tiles:         List[TileSnapshot]
    last_updated:  str


# ─────────────────────────────────────────────────────────────────────────────
# In-Memory Digital Twin
# ─────────────────────────────────────────────────────────────────────────────

# Per-tile rolling window of ValidatedPacket readings
tile_windows: dict[str, list] = defaultdict(list)

# Timestamps when each tile first crossed the Red Zone threshold
red_zone_since: dict[str, datetime] = {}

# Track which tiles have already triggered a RedZoneAlert (avoid spamming)
red_zone_alerted: dict[str, bool] = defaultdict(bool)


def aggregate_tile(tile: str) -> Optional[dict]:
    """
    Compute aggregate statistics for a tile from its rolling window.
    Returns None if the tile has no readings.
    """
    readings = tile_windows[tile]
    if not readings:
        return None

    n = len(readings)
    avg_als = round(sum(r.als_score for r in readings) / n, 4)

    # Movement context distribution
    context_counts = {"Stationary": 0, "Walking": 0, "Transit": 0}
    for r in readings:
        context_counts[r.movement_context] += 1
    context_dist = {k: round(v / n, 3) for k, v in context_counts.items()}

    # Most common noise bucket
    noise_counts = {"Low": 0, "Medium": 0, "High": 0}
    for r in readings:
        noise_counts[r.noise_bucket] += 1
    dominant_noise = max(noise_counts, key=noise_counts.get)

    # Heat flag: True if > 50% of devices flagged
    heat_count = sum(1 for r in readings if r.heat_flag)
    heat_flag = (heat_count / n) > 0.5

    # Gait quality: Degraded if > 50% of devices flagged
    gait_bad = sum(1 for r in readings if r.gait_quality == "Degraded")
    gait_quality = "Degraded" if (gait_bad / n) > 0.5 else "Good"

    return {
        "avg_als":              avg_als,
        "sample_count":         n,
        "context_distribution": context_dist,
        "noise_bucket":         dominant_noise,
        "heat_flag":            heat_flag,
        "gait_quality":         gait_quality,
    }


def get_twin_summary() -> DigitalTwinSummary:
    """Build a full snapshot of the Digital Twin for debug/dashboard use."""
    tiles = []
    for tile, readings in tile_windows.items():
        if not readings:
            continue
        stats = aggregate_tile(tile)
        tiles.append(TileSnapshot(
            h3_index=             tile,
            avg_als=              stats["avg_als"],
            sample_count=         stats["sample_count"],
            is_red_zone=          tile in red_zone_since,
            context_distribution= stats["context_distribution"],
            noise_bucket=         stats["noise_bucket"],
            heat_flag=            stats["heat_flag"],
            gait_quality=         stats["gait_quality"],
        ))

    return DigitalTwinSummary(
        active_tiles=   len(tiles),
        red_zone_count= len(red_zone_since),
        tiles=          tiles,
        last_updated=   datetime.now(timezone.utc).isoformat(),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Agent + Protocol
# ─────────────────────────────────────────────────────────────────────────────

mapping_agent = Agent(
    name="mapping_agent",
    seed=AGENT_SEEDS["mapping"],
    port=AGENT_PORTS["mapping"],
    endpoint=[f"http://127.0.0.1:{AGENT_PORTS['mapping']}/submit"],
)

mapping_proto = Protocol("mapping")


@mapping_proto.on_message(model=ValidatedPacket)
async def handle_validated_packet(ctx: Context, sender: str, msg: ValidatedPacket):
    tile = msg.h3_index

    # ── Step 1: Append to rolling tile window ────────────────────────────────
    tile_windows[tile].append(msg)
    if len(tile_windows[tile]) > TILE_WINDOW_SIZE:
        tile_windows[tile].pop(0)

    # ── Step 2: Compute tile aggregates ─────────────────────────────────────
    stats = aggregate_tile(tile)

    ctx.logger.info(
        f"📡 Tile {tile[:12]}... | "
        f"n={stats['sample_count']} | "
        f"avg_ALS={stats['avg_als']:.3f} | "
        f"{max(stats['context_distribution'], key=stats['context_distribution'].get)} dominant | "
        f"Noise={stats['noise_bucket']} | "
        f"Heat={'🌡' if stats['heat_flag'] else '–'} | "
        f"Gait={stats['gait_quality']}"
    )

    # ── Step 3: Red Zone detection ────────────────────────────────────────────
    now = datetime.now(timezone.utc)

    if stats["avg_als"] >= RED_ZONE_ALS_THRESHOLD:

        if tile not in red_zone_since:
            # First time crossing threshold — start the clock
            red_zone_since[tile] = now
            red_zone_alerted[tile] = False
            ctx.logger.warning(
                f"🟠 Red Zone EMERGING | Tile {tile[:12]}... | "
                f"ALS={stats['avg_als']:.3f} — monitoring..."
            )

        duration_min = (now - red_zone_since[tile]).total_seconds() / 60

        # Confirm and alert once the tile stays hot for RED_ZONE_DURATION_MIN
        if duration_min >= RED_ZONE_DURATION_MIN and not red_zone_alerted[tile]:
            ctx.logger.warning(
                f"🔴 Red Zone CONFIRMED | Tile {tile[:12]}... | "
                f"ALS={stats['avg_als']:.3f} | "
                f"Duration={duration_min:.1f} min | "
                f"Sending to Diagnosis Agent..."
            )

            alert = RedZoneAlert(
                h3_index=             tile,
                avg_als=              stats["avg_als"],
                sample_count=         stats["sample_count"],
                context_distribution= stats["context_distribution"],
                noise_bucket=         stats["noise_bucket"],
                heat_flag=            stats["heat_flag"],
                gait_quality=         stats["gait_quality"],
                duration_minutes=     round(duration_min, 1),
            )

            if DIAGNOSIS_AGENT_ADDRESS != "agent1q_PASTE_DIAGNOSIS_ADDRESS_HERE":
                await ctx.send(DIAGNOSIS_AGENT_ADDRESS, alert)
                red_zone_alerted[tile] = True
                ctx.logger.info(f"📤 RedZoneAlert forwarded → Diagnosis Agent")
            else:
                ctx.logger.warning(
                    "⚠️  DIAGNOSIS_AGENT_ADDRESS not set — "
                    "alert built but not forwarded."
                )

        elif duration_min >= RED_ZONE_DURATION_MIN and red_zone_alerted[tile]:
            # Re-alert every 10 minutes if the zone stays hot
            last_alert_min = (
                (now - red_zone_since[tile]).total_seconds() / 60
                - RED_ZONE_DURATION_MIN
            )
            if last_alert_min >= 10.0:
                red_zone_alerted[tile] = False   # Reset so next packet re-triggers
                ctx.logger.info(
                    f"🔄 Re-alerting Red Zone at {tile[:12]}... "
                    f"(still elevated after {duration_min:.0f} min)"
                )

    else:
        # ALS dropped below threshold — clear the Red Zone
        if tile in red_zone_since:
            duration_min = (now - red_zone_since[tile]).total_seconds() / 60
            ctx.logger.info(
                f"✅ Red Zone CLEARED | Tile {tile[:12]}... | "
                f"Was elevated for {duration_min:.1f} min"
            )
            del red_zone_since[tile]
            red_zone_alerted[tile] = False

    # ── Step 4: Log Digital Twin state ───────────────────────────────────────
    active = len([t for t in tile_windows if tile_windows[t]])
    ctx.logger.info(
        f"🗺  Digital Twin | "
        f"Active tiles: {active} | "
        f"Red Zones: {len(red_zone_since)}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Periodic Twin Health Check (every 60 seconds)
# ─────────────────────────────────────────────────────────────────────────────

@mapping_agent.on_interval(period=60.0)
async def twin_health_check(ctx: Context):
    """Log a full Digital Twin summary every 60 seconds."""
    summary = get_twin_summary()
    ctx.logger.info(
        f"🔄 Twin Heartbeat | "
        f"Tiles: {summary.active_tiles} | "
        f"Red Zones: {summary.red_zone_count} | "
        f"Updated: {summary.last_updated}"
    )
    for tile in summary.tiles:
        if tile.is_red_zone:
            ctx.logger.warning(
                f"  🔴 {tile.h3_index[:14]}... | "
                f"ALS={tile.avg_als:.3f} | "
                f"{max(tile.context_distribution, key=tile.context_distribution.get)} | "
                f"Noise={tile.noise_bucket}"
            )


# ─────────────────────────────────────────────────────────────────────────────
# Startup
# ─────────────────────────────────────────────────────────────────────────────

@mapping_agent.on_event("startup")
async def on_startup(ctx: Context):
    ctx.logger.info("━" * 55)
    ctx.logger.info("🗺  Urban Nervous System — Mapping Agent")
    ctx.logger.info(f"📍 Address   : {mapping_agent.address}")
    ctx.logger.info(f"🔌 Port      : {AGENT_PORTS['mapping']}")
    ctx.logger.info(f"🔬 Diagnosis : {DIAGNOSIS_AGENT_ADDRESS[:30]}...")
    ctx.logger.info(f"🔴 Red Zone  : ALS > {RED_ZONE_ALS_THRESHOLD} "
                    f"sustained {RED_ZONE_DURATION_MIN} min")
    ctx.logger.info(f"📦 Tile window: last {TILE_WINDOW_SIZE} readings (~"
                    f"{TILE_WINDOW_SIZE // 2} min)")
    ctx.logger.info("⏳ Waiting for validated ALS packets...")
    ctx.logger.info("━" * 55)


# ─────────────────────────────────────────────────────────────────────────────
# Register & Run
# ─────────────────────────────────────────────────────────────────────────────

mapping_agent.include(mapping_proto, publish_manifest=True)

if __name__ == "__main__":
    mapping_agent.run()
    