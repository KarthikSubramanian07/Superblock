from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd

from training.constants import LABEL_COLUMN

AXES = ("x", "y", "z")
WINDOW_METADATA_COLUMNS = ("subject_id", "raw_activity", LABEL_COLUMN)
STAT_NAMES = ("mean", "std", "min", "max", "median", "energy", "sma")
MAG_STAT_NAMES = ("mean", "std", "min", "max", "median", "energy", "sma")


def expected_feature_names() -> list[str]:
    names: list[str] = []
    for axis in AXES:
        prefix = f"accel_{axis}_"
        names.extend(f"{prefix}{stat_name}" for stat_name in STAT_NAMES)
    names.extend(f"accel_mag_{stat_name}" for stat_name in MAG_STAT_NAMES)
    return names


def _series_stats(values: np.ndarray, prefix: str) -> dict[str, float]:
    return {
        f"{prefix}mean": float(np.mean(values)),
        f"{prefix}std": float(np.std(values)),
        f"{prefix}min": float(np.min(values)),
        f"{prefix}max": float(np.max(values)),
        f"{prefix}median": float(np.median(values)),
        f"{prefix}energy": float(np.mean(np.square(values))),
        f"{prefix}sma": float(np.mean(np.abs(values))),
    }


def compute_window_features(window: pd.DataFrame) -> dict[str, float]:
    features: dict[str, float] = {}
    for axis in AXES:
        values = window[axis].to_numpy(dtype=np.float64)
        features.update(_series_stats(values, f"accel_{axis}_"))

    magnitude = np.sqrt(
        np.square(window["x"].to_numpy(dtype=np.float64))
        + np.square(window["y"].to_numpy(dtype=np.float64))
        + np.square(window["z"].to_numpy(dtype=np.float64))
    )
    features.update(_series_stats(magnitude, "accel_mag_"))
    return features


def build_windowed_features(
    samples: pd.DataFrame,
    window_size: int,
    step_size: int,
) -> pd.DataFrame:
    rows: list[dict[str, float | str | int]] = []
    grouped = samples.groupby(["subject_id", "raw_activity"], sort=True)

    for (subject_id, raw_activity), group in grouped:
        group = group.sort_values("timestamp").reset_index(drop=True)
        label = group[LABEL_COLUMN].iloc[0]

        for start_index in range(0, len(group) - window_size + 1, step_size):
            end_index = start_index + window_size
            window = group.iloc[start_index:end_index]
            feature_row = compute_window_features(window)
            feature_row["subject_id"] = str(subject_id)
            feature_row["raw_activity"] = str(raw_activity)
            feature_row[LABEL_COLUMN] = str(label)
            rows.append(feature_row)

    feature_frame = pd.DataFrame(rows)
    if feature_frame.empty:
        return feature_frame

    ordered_columns = [
        *WINDOW_METADATA_COLUMNS,
        *expected_feature_names(),
    ]
    return feature_frame[ordered_columns]


def split_features_and_labels(
    feature_frame: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Series]:
    feature_names = expected_feature_names()
    missing = [name for name in feature_names if name not in feature_frame.columns]
    if missing:
        raise ValueError(
            "Prepared dataset is missing expected feature columns: "
            + ", ".join(sorted(missing))
        )
    return feature_frame[feature_names].copy(), feature_frame[LABEL_COLUMN].copy()


def as_feature_dict(values: Iterable[float]) -> dict[str, float]:
    return {
        feature_name: float(value)
        for feature_name, value in zip(expected_feature_names(), values, strict=True)
    }
