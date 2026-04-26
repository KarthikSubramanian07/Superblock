#!/usr/bin/env python3
"""
load_demo_mirror.py
────────────────────────────────────────────────────────────────────
Mirrors the frontend mock data (peak hour = 2 PM) into the live
backend so the map looks identical to demo mode.

Each tile from mockData.json is sent as 3 edge packets with
different simulated user IDs but the same als_score / context /
noise_db — giving the aggregator a strong, accurate signal.
────────────────────────────────────────────────────────────────────
"""
import json, random, sys, requests
from datetime import datetime, timedelta, timezone
from pathlib import Path

BACKEND     = "http://127.0.0.1:8000"
MOCK_JSON   = Path(__file__).parents[3] / "superblock-ui" / "src" / "data" / "mockData.json"
PEAK_LABEL  = "2:00 PM"   # highest-stress timeframe
PACKETS_PER_TILE = 3      # enough signal without flooding the server
BATCH_SIZE  = 50


def main():
    print("=" * 60)
    print("  SUPERBLOCK — DEMO MIRROR LOADER")
    print("=" * 60)

    # ── Load mock data ───────────────────────────────────────────
    with open(MOCK_JSON) as f:
        mock = json.load(f)

    frames = {t["label"]: t for t in mock["timeframes"]}
    if PEAK_LABEL not in frames:
        print(f"ERROR: '{PEAK_LABEL}' not found. Available: {list(frames)[:5]}")
        sys.exit(1)

    tiles = frames[PEAK_LABEL]["tiles"]
    print(f"\n[1/4] Loaded {len(tiles)} tiles from mock '{PEAK_LABEL}'")

    # ── Reset backend ────────────────────────────────────────────
    print("[2/4] Resetting demo state...")
    try:
        resp = requests.post(f"{BACKEND}/demo/reset", timeout=5)
        print(f"      Reset: {resp.status_code}")
    except requests.exceptions.Timeout:
        print("      Reset timed out — continuing anyway")

    # ── Build packets ────────────────────────────────────────────
    now = datetime.now(timezone.utc)
    packets = []
    for tile in tiles:
        for i in range(PACKETS_PER_TILE):
            uid = f"mirror_u{random.randint(1, 999):04d}"
            ts  = now - timedelta(minutes=random.randint(0, 30),
                                  seconds=random.randint(0, 59))
            packets.append({
                "user_id":   uid,
                "h3_index":  tile["h3_index"],
                "als_score": tile["als_score"],
                "context":   tile["context"],
                "noise_db":  tile["noise_db"],
                "timestamp": ts.isoformat(),
            })

    random.shuffle(packets)
    print(f"[3/4] Sending {len(packets)} packets ({len(tiles)} tiles × {PACKETS_PER_TILE})...")

    sent, failed = 0, 0
    for i in range(0, len(packets), BATCH_SIZE):
        batch = packets[i : i + BATCH_SIZE]
        r = requests.post(f"{BACKEND}/ingest/edge-packets", json={"packets": batch}, timeout=10)
        if r.status_code == 200:
            sent += len(batch)
        else:
            failed += len(batch)
            print(f"      Batch {i//BATCH_SIZE+1} failed: {r.status_code} {r.text[:120]}")

    print(f"      ✅ Sent: {sent}  |  ❌ Failed: {failed}")

    # ── Verify ───────────────────────────────────────────────────
    print("[4/4] Verifying...")
    status = requests.get(f"{BACKEND}/demo/status", timeout=5).json()
    print(f"      packets={status['edge_packet_count']}  "
          f"users={status['unique_edge_users']}  "
          f"tiles={status['active_tile_count']}  "
          f"red_zones={status['red_zone_count']}")

    print("\n" + "=" * 60)
    print("  DONE — map should match demo mode within 1 second")
    print("=" * 60)


if __name__ == "__main__":
    main()
