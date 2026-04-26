#!/usr/bin/env python3
"""
generate_rich_demo_data.py
──────────────────────────────────────────────────────────────────
Generates diverse, realistic mock edge telemetry for Superblock.
Simulates 30+ users across 15+ H3 tiles spanning all of Downtown
LA with clear stress gradients — judges will see a living,
breathing urban nervous system with obvious red zones, transition
zones, and healthy green areas.
──────────────────────────────────────────────────────────────────
"""
import random
import requests
from datetime import datetime, timedelta, timezone

BACKEND = "http://127.0.0.1:8000"

# ── Downtown LA H3 tiles (resolution 9) ─────────────────────────
# Curated to cover the real neighborhoods judges would recognize
TILES = [
    # === CRITICAL STRESS — Red Zones (will trigger agent diagnosis) ===
    {"h3": "8929a19818fffff", "name": "Arts District / Industrial",  "stress": "critical",
     "story": "Extreme heat + zero shade + heavy truck traffic noise"},
    {"h3": "8929a19818bffff", "name": "Skid Row Periphery",         "stress": "critical",
     "story": "Overcrowding + degraded infrastructure + heat island"},
    {"h3": "8929a19819bffff", "name": "7th St / Metro Hub",         "stress": "critical",
     "story": "Transit congestion + pedestrian bottleneck + noise"},

    # === HIGH STRESS — Orange/Amber Zones ===
    {"h3": "8929a1981b3ffff", "name": "Pershing Square",            "stress": "high",
     "story": "High stationary dwell time + ambient construction noise"},
    {"h3": "8929a19819fffff", "name": "Bunker Hill / Grand Ave",    "stress": "high",
     "story": "Steep grade changes + gait degradation + heat exposure"},
    {"h3": "8929a1981a7ffff", "name": "Broadway Corridor",          "stress": "high",
     "story": "Dense pedestrian traffic + narrow sidewalks + heat"},

    # === MEDIUM STRESS — Yellow/Watch Zones ===
    {"h3": "8929a1981afffff", "name": "Little Tokyo",               "stress": "medium",
     "story": "Moderate foot traffic, some shade, transit proximity"},
    {"h3": "8929a1981a3ffff", "name": "Civic Center / City Hall",   "stress": "medium",
     "story": "Government district with moderate pedestrian volume"},
    {"h3": "8929a19818fffff", "name": "Central Market Block",       "stress": "medium",
     "story": "Mixed-use with food vendors, moderate crowd density"},
    {"h3": "8929a1981abffff", "name": "Spring St Corridor",         "stress": "medium",
     "story": "Historic district with moderate shade and foot traffic"},

    # === LOW STRESS — Green/Healthy Zones ===
    {"h3": "8929a1981b7ffff", "name": "Grand Park",                 "stress": "low",
     "story": "Dense tree canopy + low noise + good ventilation"},
    {"h3": "8929a1981bbffff", "name": "Disney Hall Gardens",        "stress": "low",
     "story": "Well-designed public space with shade and seating"},
    {"h3": "8929a1981a3ffff", "name": "Echo Park Edge",             "stress": "low",
     "story": "Residential buffer zone with mature urban tree cover"},
    {"h3": "8929a1981b3ffff", "name": "Figueroa Corridor South",    "stress": "low",
     "story": "Recently improved streetscape with cool pavement"},
]

CONTEXTS = ["stationary", "walking", "transit_like"]

STRESS_PROFILES = {
    "low":      {"als_range": (0.08, 0.30), "noise_range": (22, 42), "heat_prob": 0.03,
                 "context_weights": [0.25, 0.55, 0.20], "gait_degrade_prob": 0.02},
    "medium":   {"als_range": (0.35, 0.58), "noise_range": (42, 62), "heat_prob": 0.20,
                 "context_weights": [0.35, 0.45, 0.20], "gait_degrade_prob": 0.10},
    "high":     {"als_range": (0.58, 0.78), "noise_range": (62, 82), "heat_prob": 0.55,
                 "context_weights": [0.50, 0.35, 0.15], "gait_degrade_prob": 0.30},
    "critical": {"als_range": (0.78, 0.96), "noise_range": (78, 98), "heat_prob": 0.85,
                 "context_weights": [0.60, 0.30, 0.10], "gait_degrade_prob": 0.55},
}

# 30 simulated users for population diversity
USER_IDS = [f"user_dtla_{i:03d}" for i in range(1, 31)]


def generate_packet(tile: dict, user_id: str, timestamp: datetime) -> dict:
    profile = STRESS_PROFILES[tile["stress"]]
    als = round(random.uniform(*profile["als_range"]), 4)
    noise = round(random.uniform(*profile["noise_range"]), 1)
    context = random.choices(CONTEXTS, weights=profile["context_weights"], k=1)[0]

    return {
        "user_id": user_id,
        "h3_index": tile["h3"],
        "als_score": als,
        "context": context,
        "noise_db": noise,
        "timestamp": timestamp.isoformat(),
        "inference_engine": "onnxruntime_npu_sim",
    }


def main():
    print("=" * 60)
    print("  🏙️  SUPERBLOCK RICH DEMO DATA GENERATOR")
    print("=" * 60)

    # Reset
    print("\n[1/4] Resetting demo state...")
    resp = requests.post(f"{BACKEND}/demo/reset")
    print(f"  Reset: {resp.status_code}")

    # Generate packets — critical tiles get more data for stronger signal
    now = datetime.now(timezone.utc)
    all_packets = []
    packets_per_stress = {"critical": 18, "high": 14, "medium": 10, "low": 8}

    for tile in TILES:
        n_packets = packets_per_stress[tile["stress"]]
        tile_users = random.sample(USER_IDS, min(n_packets, len(USER_IDS)))

        for i in range(n_packets):
            user = tile_users[i % len(tile_users)]
            # Spread timestamps over last 30 minutes for realism
            ts = now - timedelta(minutes=random.randint(0, 30), seconds=random.randint(0, 59))
            pkt = generate_packet(tile, user, ts)
            all_packets.append(pkt)

    random.shuffle(all_packets)
    print(f"\n[2/4] Generated {len(all_packets)} packets across {len(TILES)} tiles")

    # Send in batches
    print(f"\n[3/4] Sending to backend...")
    batch_size = 5
    sent = 0
    failed = 0
    for i in range(0, len(all_packets), batch_size):
        batch = all_packets[i : i + batch_size]
        resp = requests.post(f"{BACKEND}/ingest/edge-packets", json={"packets": batch})
        if resp.status_code == 200:
            sent += len(batch)
        else:
            failed += len(batch)

    print(f"  ✅ Sent: {sent}  |  ❌ Failed: {failed}")

    # Verify
    print(f"\n[4/4] Verifying system state...")
    status = requests.get(f"{BACKEND}/demo/status").json()
    mongo = requests.get(f"{BACKEND}/mongo/stats").json()

    print(f"  📦 Edge packets:    {status['edge_packet_count']}")
    print(f"  👤 Unique users:    {status['unique_edge_users']}")
    print(f"  🗺️  Active tiles:    {status['active_tile_count']}")
    print(f"  🔥 Hotspots:        {status['hotspot_count']}")
    print(f"  🔴 Red zones:       {status['red_zone_count']}")
    print(f"  🍃 MongoDB packets: {mongo.get('total_packets', 'N/A')}")

    # Test orchestration with the rich data
    print(f"\n  Testing agent orchestration...")
    orch = requests.post(f"{BACKEND}/agents/orchestrate", json={})
    if orch.status_code == 200:
        data = orch.json()
        diag = data.get("diagnosis_alert", {})
        print(f"  🧠 Top hotspot:     {data.get('selected_h3_index', '?')}")
        print(f"  📊 Avg ALS:         {diag.get('avg_als', '?')}")
    else:
        print(f"  ⚠️  Orchestration: {orch.status_code}")

    print("\n" + "=" * 60)
    print("  ✨ DEMO DATA READY")
    print("  🌐 Frontend: http://localhost:5174/")
    print("  📡 Backend:  http://localhost:8000/demo/status")
    print("=" * 60)


if __name__ == "__main__":
    main()
