from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel


class Settings(BaseModel):
    base_dir: Path = Path(__file__).resolve().parent.parent
    artifacts_dir: Path = base_dir / "artifacts"
    model_path: Path = artifacts_dir / "model.joblib"
    metadata_path: Path = artifacts_dir / "metadata.json"
    feature_names_path: Path = artifacts_dir / "feature_names.json"
    metrics_path: Path = artifacts_dir / "metrics.json"
    model_version: str = "context-classifier-v1"
    als_artifacts_dir: Path = artifacts_dir / "als"
    als_model_path: Path = als_artifacts_dir / "model.joblib"
    als_metadata_path: Path = als_artifacts_dir / "metadata.json"
    als_feature_names_path: Path = als_artifacts_dir / "feature_names.json"
    als_metrics_path: Path = als_artifacts_dir / "metrics.json"
    als_model_version: str = "als-regressor-v1"
    agent_system_dir: Path | None = None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
