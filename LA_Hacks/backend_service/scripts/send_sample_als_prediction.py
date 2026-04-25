from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd
import requests

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from training.als_constants import ALS_FEATURE_NAMES


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Send one or more prepared ALS rows to the ALS prediction API."
    )
    parser.add_argument("--csv", required=True, help="Path to the prepared ALS feature CSV.")
    parser.add_argument("--row-index", type=int, default=0, help="Starting row index.")
    parser.add_argument("--count", type=int, default=1, help="Number of consecutive rows to send.")
    parser.add_argument("--url", default="http://127.0.0.1:8000/predict/als", help="ALS prediction endpoint URL.")
    parser.add_argument("--session-id", default=None, help="Optional session id for server-side smoothing.")
    parser.add_argument("--smoothing-window", type=int, default=3, help="Smoothing window when session-id is provided.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    frame = pd.read_csv(Path(args.csv).expanduser().resolve())
    if args.count < 1:
        raise ValueError("count must be at least 1")
    if args.row_index < 0 or args.row_index + args.count > len(frame):
        raise IndexError("Requested ALS rows are out of range.")

    for index in range(args.row_index, args.row_index + args.count):
        row = frame.iloc[index]
        payload = {
            "window_id": f"als_row_{index}",
            "features": {
                feature_name: float(row[feature_name])
                for feature_name in ALS_FEATURE_NAMES
                if feature_name in row and pd.notna(row[feature_name])
            },
        }
        if args.session_id:
            payload["session_id"] = args.session_id
            payload["smoothing_window"] = args.smoothing_window

        response = requests.post(args.url, json=payload, timeout=30)
        response.raise_for_status()
        print(f"row_index: {index}")
        print(json.dumps(response.json(), indent=2))
        if index < args.row_index + args.count - 1:
            print()


if __name__ == "__main__":
    main()
