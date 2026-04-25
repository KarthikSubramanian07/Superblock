from __future__ import annotations

from pathlib import Path

from training.constants import BASE_DIR

ALS_FEATURE_NAMES = [
    "hrv_rmssd",
    "hrv_sdnn",
    "hrv_pnn50",
    "hr_mean",
    "hr_variance",
    "skin_temp_delta",
    "ambient_noise_db",
    "accel_intensity_mean",
]

ALS_DEFAULT_ARTIFACTS_DIR = BASE_DIR / "artifacts" / "als"
ALS_MODEL_VERSION = "als-regressor-v1"

WESAD_LABEL_TO_ALS = {
    1: 0.15,  # baseline
    2: 0.85,  # stress
    3: 0.35,  # amusement
}

STRING_LABEL_TO_ALS = {
    "baseline": 0.15,
    "stress": 0.85,
    "amusement": 0.35,
    "meditation": 0.10,
}

ALS_BAND_THRESHOLDS = {
    "low": 0.33,
    "elevated": 0.66,
}


def als_band(score: float) -> str:
    if score < ALS_BAND_THRESHOLDS["low"]:
        return "low"
    if score < ALS_BAND_THRESHOLDS["elevated"]:
        return "elevated"
    return "high"
