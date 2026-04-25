from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import GroupShuffleSplit

from training.constants import DEFAULT_ARTIFACTS_DIR
from training.features import expected_feature_names, split_features_and_labels

try:
    from lightgbm import LGBMClassifier
except (ImportError, OSError):  # pragma: no cover - exercised via runtime fallback
    LGBMClassifier = None


def build_classifier(random_state: int = 42) -> tuple[Any, str]:
    if LGBMClassifier is not None:
        classifier = LGBMClassifier(
            n_estimators=250,
            learning_rate=0.05,
            num_leaves=31,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=random_state,
        )
        return classifier, "LightGBM"

    classifier = RandomForestClassifier(
        n_estimators=300,
        random_state=random_state,
        class_weight="balanced",
        n_jobs=-1,
    )
    return classifier, "RandomForestClassifier"


def train_classifier(
    prepared_features: pd.DataFrame,
    artifacts_dir: Path = DEFAULT_ARTIFACTS_DIR,
    model_version: str = "context-classifier-v1",
    test_size: float = 0.2,
    random_state: int = 42,
) -> dict[str, Any]:
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    if "subject_id" not in prepared_features.columns:
        raise ValueError("Prepared features must include a subject_id column for subject-wise splitting.")

    x_frame, y_series = split_features_and_labels(prepared_features)
    groups = prepared_features["subject_id"].astype(str)
    unique_subjects = sorted(groups.unique().tolist())
    if len(unique_subjects) < 2:
        raise ValueError("At least two unique subjects are required for subject-wise splitting.")

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

    classifier, classifier_name = build_classifier(random_state=random_state)
    classifier.fit(x_train, y_train)

    predictions = classifier.predict(x_test)
    metrics = {
        "model_version": model_version,
        "classifier_name": classifier_name,
        "accuracy": float(accuracy_score(y_test, predictions)),
        "macro_f1": float(f1_score(y_test, predictions, average="macro")),
        "weighted_f1": float(f1_score(y_test, predictions, average="weighted")),
        "train_rows": int(len(x_train)),
        "test_rows": int(len(x_test)),
        "split_strategy": "subject_wise_group_shuffle_split",
        "train_subject_count": int(len(train_subjects)),
        "test_subject_count": int(len(test_subjects)),
        "train_subject_ids": train_subjects,
        "test_subject_ids": test_subjects,
        "class_counts": {str(label): int(count) for label, count in y_series.value_counts().items()},
        "classification_report": classification_report(
            y_test,
            predictions,
            output_dict=True,
            zero_division=0,
        ),
    }

    metadata = {
        "model_version": model_version,
        "classifier_name": classifier_name,
        "classes": [str(label) for label in classifier.classes_],
    }

    with (artifacts_dir / "model.joblib").open("wb") as handle:
        joblib.dump(classifier, handle)

    with (artifacts_dir / "metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)

    with (artifacts_dir / "feature_names.json").open("w", encoding="utf-8") as handle:
        json.dump(expected_feature_names(), handle, indent=2)

    with (artifacts_dir / "metrics.json").open("w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2)

    return metrics


def evaluate_classifier(
    prepared_features: pd.DataFrame,
    artifacts_dir: Path = DEFAULT_ARTIFACTS_DIR,
) -> dict[str, Any]:
    model_path = artifacts_dir / "model.joblib"
    metadata_path = artifacts_dir / "metadata.json"
    if not model_path.exists() or not metadata_path.exists():
        raise FileNotFoundError(
            f"Missing artifacts in {artifacts_dir}. Train the model before evaluation."
        )

    classifier = joblib.load(model_path)
    x_frame, y_series = split_features_and_labels(prepared_features)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    test_subject_ids = metadata.get("test_subject_ids", [])
    if test_subject_ids and "subject_id" in prepared_features.columns:
        mask = prepared_features["subject_id"].astype(str).isin(test_subject_ids)
        evaluation_frame = x_frame.loc[mask]
        evaluation_labels = y_series.loc[mask]
    else:
        evaluation_frame = x_frame
        evaluation_labels = y_series

    predictions = classifier.predict(evaluation_frame)

    return {
        "accuracy": float(accuracy_score(evaluation_labels, predictions)),
        "macro_f1": float(f1_score(evaluation_labels, predictions, average="macro")),
        "weighted_f1": float(f1_score(evaluation_labels, predictions, average="weighted")),
        "rows": int(len(evaluation_frame)),
        "classes": sorted({str(item) for item in evaluation_labels.unique()}),
        "evaluation_scope": "held_out_subjects" if test_subject_ids else "full_dataset",
    }
