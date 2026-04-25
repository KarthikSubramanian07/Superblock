from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable

import joblib
import numpy as np
import pandas as pd

from app.als_feature_contract import complete_als_feature_payload
from app.settings import get_settings
from training.als_constants import ALS_FEATURE_NAMES, als_band


@dataclass(frozen=True)
class LoadedAlsModel:
    regressor: object
    regressor_name: str
    feature_names: list[str]
    model_version: str
    training_metrics: dict


class MissingAlsArtifactsError(RuntimeError):
    """Raised when ALS artifacts are not present."""


def _load_json(path: Path) -> dict | list:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=1)
def get_loaded_als_model() -> LoadedAlsModel:
    settings = get_settings()
    required_paths = [
        settings.als_model_path,
        settings.als_metadata_path,
        settings.als_feature_names_path,
        settings.als_metrics_path,
    ]
    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        raise MissingAlsArtifactsError(
            "ALS artifacts are missing. Expected files: " + ", ".join(missing)
        )

    regressor = joblib.load(settings.als_model_path)
    metadata = _load_json(settings.als_metadata_path)
    metrics = _load_json(settings.als_metrics_path)
    feature_names = _load_json(settings.als_feature_names_path)
    return LoadedAlsModel(
        regressor=regressor,
        regressor_name=metadata["regressor_name"],
        feature_names=list(feature_names),
        model_version=metadata.get("model_version", settings.als_model_version),
        training_metrics=metrics,
    )


def reload_loaded_als_model() -> None:
    get_loaded_als_model.cache_clear()


def _build_matrix(items: Iterable[dict[str, float]]) -> pd.DataFrame:
    loaded = get_loaded_als_model()
    rows = []
    for item in items:
        completed = complete_als_feature_payload(item)
        rows.append([completed[name] for name in loaded.feature_names])
    return pd.DataFrame(np.asarray(rows, dtype=np.float64), columns=loaded.feature_names)


def predict_als_scores(items: Iterable[dict[str, float]]) -> list[float]:
    loaded = get_loaded_als_model()
    matrix = _build_matrix(items)
    predictions = np.clip(loaded.regressor.predict(matrix), 0.0, 1.0)
    return [float(score) for score in predictions]


def score_to_band(score: float) -> str:
    return als_band(score)
