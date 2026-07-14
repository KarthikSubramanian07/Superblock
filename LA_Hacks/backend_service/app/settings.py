from __future__ import annotations

import os
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

    # Auth0 Configuration
    auth0_domain: str = os.getenv("AUTH0_DOMAIN", "")
    auth0_audience: str = os.getenv("AUTH0_AUDIENCE", "")

    # AI Configuration
    asi_one_api_key: str = os.getenv("ASI_ONE_API_KEY", "")

    # Security / ops
    demo_mode: bool = os.getenv("DEMO_MODE", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    allowed_origins: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173",
        ).split(",")
        if origin.strip()
    ]
    max_edge_packets: int = int(os.getenv("MAX_EDGE_PACKETS", "50000"))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
