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

from training.constants import LABEL_COLUMN
from training.features import expected_feature_names


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Send one prepared feature row to the context prediction API."
    )
    parser.add_argument(
        "--csv",
        default="data/context_features.csv",
        help="Path to the prepared feature CSV.",
    )
    parser.add_argument(
        "--row-index",
        type=int,
        default=0,
        help="Row index from the prepared CSV to send.",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Number of consecutive rows to send starting at row-index.",
    )
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:8000/predict/context",
        help="Prediction endpoint URL.",
    )
    parser.add_argument(
        "--session-id",
        default=None,
        help="Optional session id to enable server-side smoothing on /predict/context.",
    )
    parser.add_argument(
        "--smoothing-window",
        type=int,
        default=3,
        help="Rolling smoothing window to use when session-id is provided.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    csv_path = Path(args.csv).expanduser().resolve()
    frame = pd.read_csv(csv_path)

    if frame.empty:
        raise ValueError(f"Prepared CSV is empty: {csv_path}")
    if args.row_index < 0 or args.row_index >= len(frame):
        raise IndexError(f"row-index {args.row_index} is out of range for {len(frame)} rows")
    if args.count < 1:
        raise ValueError("count must be at least 1")
    if args.row_index + args.count > len(frame):
        raise IndexError(
            f"Requested rows {args.row_index}..{args.row_index + args.count - 1} exceed CSV length {len(frame)}"
        )

    feature_names = expected_feature_names()
    for index in range(args.row_index, args.row_index + args.count):
        row = frame.iloc[index]
        payload = {
            "window_id": f"sample_row_{index}",
            "features": {name: float(row[name]) for name in feature_names},
        }
        if args.session_id:
            payload["session_id"] = args.session_id
            payload["smoothing_window"] = args.smoothing_window

        response = requests.post(args.url, json=payload, timeout=30)
        response.raise_for_status()

        print(f"row_index: {index}")
        print("expected_label:", row.get(LABEL_COLUMN, "unknown"))
        print(json.dumps(response.json(), indent=2))
        if index < args.row_index + args.count - 1:
            print()


if __name__ == "__main__":
    main()
