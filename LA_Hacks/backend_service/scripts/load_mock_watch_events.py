from __future__ import annotations

import argparse
import json
from pathlib import Path

import requests


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bulk-load synthetic Apple Watch events into the ingestion API.",
    )
    parser.add_argument(
        "--json",
        default="living_city_mock_data/mock_events.json",
        help="Path to the JSON file containing user event batches.",
    )
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:8000/ingest/watch-events",
        help="Ingestion endpoint URL.",
    )
    parser.add_argument(
        "--limit-users",
        type=int,
        default=None,
        help="Optional number of users to ingest from the file.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    json_path = Path(args.json).expanduser().resolve()
    payload = json.loads(json_path.read_text())

    if not isinstance(payload, list):
        raise ValueError("Expected top-level JSON array of {user_id, events} objects.")

    users = payload[: args.limit_users] if args.limit_users is not None else payload
    if not users:
        raise ValueError("No users found to ingest.")

    total_events = 0
    for index, user_payload in enumerate(users, start=1):
        response = requests.post(args.url, json=user_payload, timeout=120)
        response.raise_for_status()
        body = response.json()
        total_events += int(body["accepted_events"])
        print(
            f"[{index}/{len(users)}] {body['user_id']}: "
            f"accepted={body['accepted_events']} stored={body['stored_events']}"
        )

    print(f"Loaded {len(users)} users and {total_events} events from {json_path}.")


if __name__ == "__main__":
    main()
