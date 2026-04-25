from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupShuffleSplit

from training.als_constants import (
    ALS_DEFAULT_ARTIFACTS_DIR,
    ALS_FEATURE_NAMES,
    ALS_MODEL_VERSION,
    STRING_LABEL_TO_ALS,
    WESAD_LABEL_TO_ALS,
)

try:
    from lightgbm import LGBMRegressor
except (ImportError, OSError):  # pragma: no cover
    LGBMRegressor = None


def build_als_regressor(random_state: int = 42) -> tuple[Any, str]:
    if LGBMRegressor is not None:
        regressor = LGBMRegressor(
            n_estimators=250,
            learning_rate=0.05,
            num_leaves=31,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=random_state,
        )
        return regressor, "LightGBMRegressor"

    regressor = RandomForestRegressor(
        n_estimators=300,
        random_state=random_state,
        n_jobs=-1,
    )
    return regressor, "RandomForestRegressor"


def _resolve_target_series(prepared_features: pd.DataFrame) -> pd.Series:
    if "als_target" in prepared_features.columns:
        return prepared_features["als_target"].astype(float)

    for column_name in ("stress_label", "stress_state", "label"):
        if column_name in prepared_features.columns:
            values = prepared_features[column_name]
            if pd.api.types.is_numeric_dtype(values):
                mapped = values.astype(int).map(WESAD_LABEL_TO_ALS)
            else:
                mapped = values.astype(str).str.lower().map(STRING_LABEL_TO_ALS)
            if mapped.isna().any():
                unknown = sorted(set(values[mapped.isna()].astype(str).tolist()))
                raise ValueError(
                    f"Unsupported ALS label values in {column_name}: {', '.join(unknown)}"
                )
            return mapped.astype(float)

    raise ValueError(
        "Prepared ALS dataset must include one of: als_target, stress_label, stress_state, label."
    )


def _validate_feature_columns(prepared_features: pd.DataFrame) -> None:
    missing = [name for name in ALS_FEATURE_NAMES if name not in prepared_features.columns]
    if missing:
        raise ValueError(
            "Prepared ALS dataset is missing expected feature columns: "
            + ", ".join(sorted(missing))
        )
    if "subject_id" not in prepared_features.columns:
        raise ValueError("Prepared ALS dataset must include subject_id for subject-wise splitting.")


def train_als_regressor(
    prepared_features: pd.DataFrame,
    artifacts_dir: Path = ALS_DEFAULT_ARTIFACTS_DIR,
    model_version: str = ALS_MODEL_VERSION,
    test_size: float = 0.2,
    random_state: int = 42,
) -> dict[str, Any]:
    _validate_feature_columns(prepared_features)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    x_frame = prepared_features[ALS_FEATURE_NAMES].astype(float).copy()
    y_series = _resolve_target_series(prepared_features)
    groups = prepared_features["subject_id"].astype(str)

    unique_subjects = sorted(groups.unique().tolist())
    if len(unique_subjects) < 2:
        raise ValueError("At least two unique subjects are required for subject-wise ALS splitting.")

    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=test_size,
        random_state=random_state,
    )
    train_indices, test_indices = next(splitter.split(x_frame, y_series, groups))
    x_train = x_frame.iloc[train_indices]
    x_test = x_frame.iloc[test_indices]
    y_train = y_series.iloc[train_indices]
    y_test = y_series.iloc[test_indices]
    train_subjects = sorted(groups.iloc[train_indices].unique().tolist())
    test_subjects = sorted(groups.iloc[test_indices].unique().tolist())

    regressor, regressor_name = build_als_regressor(random_state=random_state)
    regressor.fit(x_train, y_train)
    predictions = np.clip(regressor.predict(x_test), 0.0, 1.0)

    metrics = {
        "model_version": model_version,
        "regressor_name": regressor_name,
        "mae": float(mean_absolute_error(y_test, predictions)),
        "rmse": float(np.sqrt(mean_squared_error(y_test, predictions))),
        "r2": float(r2_score(y_test, predictions)),
        "train_rows": int(len(x_train)),
        "test_rows": int(len(x_test)),
        "split_strategy": "subject_wise_group_shuffle_split",
        "train_subject_count": int(len(train_subjects)),
        "test_subject_count": int(len(test_subjects)),
        "train_subject_ids": train_subjects,
        "test_subject_ids": test_subjects,
        "target_summary": {
            "min": float(y_series.min()),
            "max": float(y_series.max()),
            "mean": float(y_series.mean()),
        },
    }

    metadata = {
        "model_version": model_version,
        "regressor_name": regressor_name,
        "feature_names": ALS_FEATURE_NAMES,
        "test_subject_ids": test_subjects,
    }

    joblib.dump(regressor, artifacts_dir / "model.joblib")
    (artifacts_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    (artifacts_dir / "feature_names.json").write_text(json.dumps(ALS_FEATURE_NAMES, indent=2), encoding="utf-8")
    (artifacts_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


def evaluate_als_regressor(
    prepared_features: pd.DataFrame,
    artifacts_dir: Path = ALS_DEFAULT_ARTIFACTS_DIR,
) -> dict[str, Any]:
    _validate_feature_columns(prepared_features)
    model_path = artifacts_dir / "model.joblib"
    metadata_path = artifacts_dir / "metadata.json"
    if not model_path.exists() or not metadata_path.exists():
        raise FileNotFoundError(
            f"Missing ALS artifacts in {artifacts_dir}. Train the model before evaluation."
        )

    regressor = joblib.load(model_path)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    x_frame = prepared_features[ALS_FEATURE_NAMES].astype(float).copy()
    y_series = _resolve_target_series(prepared_features)
    test_subject_ids = metadata.get("test_subject_ids", [])

    if test_subject_ids:
        mask = prepared_features["subject_id"].astype(str).isin(test_subject_ids)
        x_frame = x_frame.loc[mask]
        y_series = y_series.loc[mask]

    predictions = np.clip(regressor.predict(x_frame), 0.0, 1.0)
    return {
        "mae": float(mean_absolute_error(y_series, predictions)),
        "rmse": float(np.sqrt(mean_squared_error(y_series, predictions))),
        "r2": float(r2_score(y_series, predictions)),
        "rows": int(len(x_frame)),
        "evaluation_scope": "held_out_subjects" if test_subject_ids else "full_dataset",
    }
