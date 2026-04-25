from __future__ import annotations

import math

from training.als_constants import ALS_FEATURE_NAMES

ALS_DEFAULT_FILL_VALUE = 0.0

ALS_FEATURE_LIMITS: dict[str, tuple[float | None, float | None]] = {
    "hrv_rmssd": (0.0, 500.0),
    "hrv_sdnn": (0.0, 500.0),
    "hrv_pnn50": (0.0, 100.0),
    "hr_mean": (20.0, 240.0),
    "hr_variance": (0.0, 10000.0),
    "skin_temp_delta": (-10.0, 10.0),
    "ambient_noise_db": (0.0, 140.0),
    "accel_intensity_mean": (0.0, 50.0),
}


def validate_als_feature_payload(features: dict[str, float]) -> None:
    extra = [name for name in features if name not in ALS_FEATURE_LIMITS]
    if extra:
        raise ValueError("Unexpected ALS features provided: " + ", ".join(sorted(extra)))

    for feature_name, raw_value in features.items():
        value = float(raw_value)
        if not math.isfinite(value):
            raise ValueError(f"ALS feature {feature_name} must be finite.")
        minimum, maximum = ALS_FEATURE_LIMITS[feature_name]
        if minimum is not None and value < minimum:
            raise ValueError(f"ALS feature {feature_name} must be >= {minimum}, got {value}.")
        if maximum is not None and value > maximum:
            raise ValueError(f"ALS feature {feature_name} must be <= {maximum}, got {value}.")


def complete_als_feature_payload(features: dict[str, float]) -> dict[str, float]:
    completed = {name: ALS_DEFAULT_FILL_VALUE for name in ALS_FEATURE_NAMES}
    completed.update({name: float(value) for name, value in features.items()})
    return completed
