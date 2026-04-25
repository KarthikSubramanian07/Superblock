from __future__ import annotations

import argparse
import json
from pathlib import Path

import requests


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert mock watch events into privacy-safe packets and ingest them.",
    )
    parser.add_argument(
        "--json",
        default="living_city_mock_data/mock_events.json",
        help="Path to the mock watch events JSON file.",
    )
    parser.add_argument(
        "--predict-url",
        default="http://127.0.0.1:8000/predict/als/watch/privacy-packets",
        help="Watch-sequence privacy packet endpoint.",
    )
    parser.add_argument(
        "--ingest-url",
        default="http://127.0.0.1:8000/ingest/edge-packets",
        help="Privacy packet ingestion endpoint.",
    )
    parser.add_argument(
        "--limit-users",
        type=int,
        default=None,
        help="Optional number of users to process.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    payload = json.loads(Path(args.json).expanduser().resolve().read_text())
    if not isinstance(payload, list):
        raise ValueError("Expected a JSON array of user event batches.")

    users = payload[: args.limit_users] if args.limit_users is not None else payload
    total_packets = 0
    for index, user_payload in enumerate(users, start=1):
        predict_response = requests.post(args.predict_url, json=user_payload, timeout=120)
        predict_response.raise_for_status()
        packets = predict_response.json()["packets"]

        ingest_response = requests.post(
            args.ingest_url,
            json={"packets": packets},
            timeout=120,
        )
        ingest_response.raise_for_status()

        total_packets += len(packets)
        print(
            f"[{index}/{len(users)}] {user_payload['user_id']}: "
            f"generated={len(packets)} packets"
        )

    print(f"Loaded {total_packets} privacy-safe packets from {len(users)} users.")


if __name__ == "__main__":
    main()
