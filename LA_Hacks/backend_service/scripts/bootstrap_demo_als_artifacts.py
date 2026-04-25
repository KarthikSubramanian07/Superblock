from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from training.als_modeling import train_als_regressor


def build_demo_als_frame(rows_per_subject: int = 24) -> pd.DataFrame:
    rows = []
    subject_targets = {
        "s1": 0.15,
        "s2": 0.25,
        "s3": 0.40,
        "s4": 0.55,
        "s5": 0.70,
        "s6": 0.85,
        "s7": 0.30,
        "s8": 0.78,
    }
    for subject_index, (subject_id, target) in enumerate(subject_targets.items(), start=1):
        for row_index in range(rows_per_subject):
            load_drift = row_index * 0.04
            rows.append(
                {
                    "subject_id": subject_id,
                    "als_target": target,
                    "hrv_rmssd": 54.0 - (target * 22.0) + load_drift,
                    "hrv_sdnn": 42.0 - (target * 14.0) + (row_index * 0.03),
                    "hrv_pnn50": 30.0 - (target * 12.0) + (row_index * 0.02),
                    "hr_mean": 68.0 + (target * 38.0) + (row_index * 0.12),
                    "hr_variance": 4.0 + (target * 12.0) + (row_index * 0.05),
                    "skin_temp_delta": -0.4 + (target * 1.8),
                    "ambient_noise_db": 44.0 + (target * 28.0),
                    "accel_intensity_mean": 0.15 + (subject_index * 0.08) + (target * 0.2),
                }
            )
    return pd.DataFrame(rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate demo ALS artifacts for local development and hackathon demos.",
    )
    parser.add_argument(
        "--output-csv",
        default="data/als_features_demo.csv",
        help="Where to save the generated demo ALS CSV.",
    )
    parser.add_argument(
        "--artifacts-dir",
        default="artifacts/als",
        help="Where to write the trained ALS artifacts.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    output_csv = Path(args.output_csv).expanduser().resolve()
    artifacts_dir = Path(args.artifacts_dir).expanduser().resolve()

    frame = build_demo_als_frame()
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_csv, index=False)

    metrics = train_als_regressor(frame, artifacts_dir=artifacts_dir)
    print(
        json.dumps(
            {
                "prepared_csv": str(output_csv),
                "artifacts_dir": str(artifacts_dir),
                "metrics": metrics,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
