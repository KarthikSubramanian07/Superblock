from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Sequence

import joblib
import numpy as np
import pandas as pd

from app.feature_contract import complete_feature_payload
from app.settings import get_settings


@dataclass(frozen=True)
class LoadedModel:
    classifier: object
    classifier_name: str
    classes: list[str]
    feature_names: list[str]
    model_version: str
    training_metrics: dict


class MissingArtifactsError(RuntimeError):
    """Raised when model artifacts are not present."""


def _load_json(path: Path) -> dict | list:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=1)
def get_loaded_model() -> LoadedModel:
    settings = get_settings()

    required_paths = [
        settings.model_path,
        settings.metadata_path,
        settings.feature_names_path,
        settings.metrics_path,
    ]
    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        raise MissingArtifactsError(
            "Model artifacts are missing. Expected files: " + ", ".join(missing)
        )

    classifier = joblib.load(settings.model_path)
    metadata = _load_json(settings.metadata_path)
    feature_names = _load_json(settings.feature_names_path)
    metrics = _load_json(settings.metrics_path)

    return LoadedModel(
        classifier=classifier,
        classifier_name=metadata["classifier_name"],
        classes=list(metadata["classes"]),
        feature_names=list(feature_names),
        model_version=metadata.get("model_version", settings.model_version),
        training_metrics=metrics,
    )


def reload_loaded_model() -> None:
    get_loaded_model.cache_clear()


def _coerce_feature_row(features: dict[str, float], expected_features: Sequence[str]) -> list[float]:
    completed_features = complete_feature_payload(features)
    return [float(completed_features[feature]) for feature in expected_features]


def prepare_feature_matrix(items: Iterable[dict[str, float]]) -> np.ndarray:
    loaded = get_loaded_model()
    rows = [_coerce_feature_row(item, loaded.feature_names) for item in items]
    return pd.DataFrame(
        np.asarray(rows, dtype=np.float64),
        columns=loaded.feature_names,
    )


def predict_probabilities(items: Iterable[dict[str, float]]) -> list[dict[str, float]]:
    loaded = get_loaded_model()
    matrix = prepare_feature_matrix(items)
    probabilities = loaded.classifier.predict_proba(matrix)

    results: list[dict[str, float]] = []
    for row in probabilities:
        results.append(
            {
                class_name: float(score)
                for class_name, score in zip(loaded.classes, row, strict=True)
            }
        )
    return results


def predict_classes(items: Iterable[dict[str, float]]) -> list[str]:
    loaded = get_loaded_model()
    matrix = prepare_feature_matrix(items)
    predictions = loaded.classifier.predict(matrix)
    return [str(prediction) for prediction in predictions]


def smooth_probabilities(
    probabilities: Sequence[dict[str, float]],
    classes: Sequence[str],
    smoothing_window: int,
) -> list[dict[str, float]]:
    smoothed: list[dict[str, float]] = []
    for index in range(len(probabilities)):
        start_index = max(0, index - smoothing_window + 1)
        window = probabilities[start_index : index + 1]
        averaged = {
            class_name: float(
                sum(item[class_name] for item in window) / len(window)
            )
            for class_name in classes
        }
        smoothed.append(averaged)
    return smoothed


def probabilities_to_classes(
    probabilities: Sequence[dict[str, float]],
    classes: Sequence[str],
) -> list[str]:
    results: list[str] = []
    for item in probabilities:
        best_class = max(classes, key=lambda class_name: item[class_name])
        results.append(best_class)
    return results
