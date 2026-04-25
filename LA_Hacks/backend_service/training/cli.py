from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from training.als_constants import ALS_DEFAULT_ARTIFACTS_DIR, ALS_MODEL_VERSION
from training.als_modeling import evaluate_als_regressor, train_als_regressor
from training.constants import DEFAULT_ARTIFACTS_DIR, DEFAULT_DATASET_URL, DEFAULT_DATA_DIR
from training.dataset import ensure_wisdm_download, load_watch_accel_samples
from training.features import build_windowed_features
from training.modeling import evaluate_classifier, train_classifier


def _prepared_csv_path(value: str | None) -> Path | None:
    if value is None:
        return None
    return Path(value).expanduser().resolve()


def prepare_dataset(
    output_csv: Path,
    raw_dir: Path | None = None,
    data_dir: Path = DEFAULT_DATA_DIR,
    dataset_url: str = DEFAULT_DATASET_URL,
    window_size: int = 200,
    step_size: int = 100,
) -> Path:
    if raw_dir is None:
        raw_dir = ensure_wisdm_download(data_dir, dataset_url)

    samples = load_watch_accel_samples(raw_dir)
    feature_frame = build_windowed_features(
        samples=samples,
        window_size=window_size,
        step_size=step_size,
    )
    if feature_frame.empty:
        raise ValueError("No feature windows were generated. Check window size and input data.")

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    feature_frame.to_csv(output_csv, index=False)
    return output_csv


def load_or_prepare_features(
    prepared_csv: Path | None,
    raw_dir: Path | None,
    data_dir: Path,
    dataset_url: str,
    window_size: int,
    step_size: int,
) -> pd.DataFrame:
    if prepared_csv is not None:
        return pd.read_csv(prepared_csv)

    temp_output = data_dir / "context_features.csv"
    prepare_dataset(
        output_csv=temp_output,
        raw_dir=raw_dir,
        data_dir=data_dir,
        dataset_url=dataset_url,
        window_size=window_size,
        step_size=step_size,
    )
    return pd.read_csv(temp_output)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Context classifier training CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare_parser = subparsers.add_parser("prepare", help="Build a prepared feature CSV")
    prepare_parser.add_argument("--output-csv", required=True)
    prepare_parser.add_argument("--raw-dir", default=None)
    prepare_parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    prepare_parser.add_argument("--dataset-url", default=DEFAULT_DATASET_URL)
    prepare_parser.add_argument("--window-size", type=int, default=200)
    prepare_parser.add_argument("--step-size", type=int, default=100)

    train_parser = subparsers.add_parser("train", help="Train and persist model artifacts")
    train_parser.add_argument("--prepared-csv", default=None)
    train_parser.add_argument("--raw-dir", default=None)
    train_parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    train_parser.add_argument("--dataset-url", default=DEFAULT_DATASET_URL)
    train_parser.add_argument("--window-size", type=int, default=200)
    train_parser.add_argument("--step-size", type=int, default=100)
    train_parser.add_argument("--artifacts-dir", default=str(DEFAULT_ARTIFACTS_DIR))
    train_parser.add_argument("--model-version", default="context-classifier-v1")

    evaluate_parser = subparsers.add_parser("evaluate", help="Evaluate a saved model")
    evaluate_parser.add_argument("--prepared-csv", required=True)
    evaluate_parser.add_argument("--artifacts-dir", default=str(DEFAULT_ARTIFACTS_DIR))

    als_train_parser = subparsers.add_parser("train-als", help="Train ALS regressor artifacts")
    als_train_parser.add_argument("--prepared-csv", required=True)
    als_train_parser.add_argument("--artifacts-dir", default=str(ALS_DEFAULT_ARTIFACTS_DIR))
    als_train_parser.add_argument("--model-version", default=ALS_MODEL_VERSION)

    als_evaluate_parser = subparsers.add_parser("evaluate-als", help="Evaluate a saved ALS model")
    als_evaluate_parser.add_argument("--prepared-csv", required=True)
    als_evaluate_parser.add_argument("--artifacts-dir", default=str(ALS_DEFAULT_ARTIFACTS_DIR))

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "prepare":
        output_path = Path(args.output_csv).expanduser().resolve()
        raw_dir = _prepared_csv_path(args.raw_dir)
        data_dir = Path(args.data_dir).expanduser().resolve()
        prepared_path = prepare_dataset(
            output_csv=output_path,
            raw_dir=raw_dir,
            data_dir=data_dir,
            dataset_url=args.dataset_url,
            window_size=args.window_size,
            step_size=args.step_size,
        )
        print(json.dumps({"prepared_csv": str(prepared_path)}, indent=2))
        return

    if args.command == "train":
        prepared_csv = _prepared_csv_path(args.prepared_csv)
        raw_dir = _prepared_csv_path(args.raw_dir)
        data_dir = Path(args.data_dir).expanduser().resolve()
        artifacts_dir = Path(args.artifacts_dir).expanduser().resolve()
        prepared = load_or_prepare_features(
            prepared_csv=prepared_csv,
            raw_dir=raw_dir,
            data_dir=data_dir,
            dataset_url=args.dataset_url,
            window_size=args.window_size,
            step_size=args.step_size,
        )
        metrics = train_classifier(
            prepared_features=prepared,
            artifacts_dir=artifacts_dir,
            model_version=args.model_version,
        )
        print(json.dumps(metrics, indent=2))
        return

    if args.command == "evaluate":
        prepared = pd.read_csv(Path(args.prepared_csv).expanduser().resolve())
        metrics = evaluate_classifier(
            prepared_features=prepared,
            artifacts_dir=Path(args.artifacts_dir).expanduser().resolve(),
        )
        print(json.dumps(metrics, indent=2))
        return

    if args.command == "train-als":
        prepared = pd.read_csv(Path(args.prepared_csv).expanduser().resolve())
        metrics = train_als_regressor(
            prepared_features=prepared,
            artifacts_dir=Path(args.artifacts_dir).expanduser().resolve(),
            model_version=args.model_version,
        )
        print(json.dumps(metrics, indent=2))
        return

    if args.command == "evaluate-als":
        prepared = pd.read_csv(Path(args.prepared_csv).expanduser().resolve())
        metrics = evaluate_als_regressor(
            prepared_features=prepared,
            artifacts_dir=Path(args.artifacts_dir).expanduser().resolve(),
        )
        print(json.dumps(metrics, indent=2))
        return

    parser.error("Unknown command")


if __name__ == "__main__":
    main()
