from __future__ import annotations

import math
from statistics import mean

from app.als_feature_contract import ALS_FEATURE_LIMITS


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _variance(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    avg = sum(values) / len(values)
    return sum((value - avg) ** 2 for value in values) / len(values)


def derive_als_features_from_watch_sequence(
    metrics_sequence: list[dict[str, float]],
) -> list[dict[str, float]]:
    if not metrics_sequence:
        raise ValueError("metrics_sequence must contain at least one event")

    derived_rows: list[dict[str, float]] = []
    hr_history: list[float] = []
    rr_history: list[float] = []

    for metrics in metrics_sequence:
        heart_rate = float(metrics["heart_rate"])
        respiratory_rate = float(metrics["respiratory_rate"])
        sleep_hours = float(metrics["sleep"])
        physical_effort = float(metrics["physical_effort"])
        walking_speed = float(metrics["walking_speed"])
        walking_steadiness = float(metrics["walking_steadiness"])
        stair_speed = float(metrics["stair_speed"])
        stairs_up = float(metrics["stairs_up"])
        stairs_down = float(metrics["stairs_down"])
        skin_temp_delta = float(metrics["wrist_temperature"])
        ambient_noise_db = float(metrics["environmental_sound_level"])

        hr_history.append(heart_rate)
        rr_history.append(respiratory_rate)
        trailing_hr = hr_history[-5:]
        trailing_rr = rr_history[-5:]

        effort_penalty = physical_effort * 18.0
        sleep_bonus = _clamp((sleep_hours - 6.0) * 2.5, -8.0, 10.0)
        steadiness_bonus = walking_steadiness * 6.0
        rr_penalty = max(0.0, mean(trailing_rr) - 16.0) * 1.4

        # Heuristic HRV proxies derived from the available watch metrics.
        hrv_rmssd = _clamp(
            62.0
            - ((heart_rate - 60.0) * 0.55)
            - effort_penalty
            - rr_penalty
            + sleep_bonus
            + steadiness_bonus,
            *ALS_FEATURE_LIMITS["hrv_rmssd"],
        )
        hrv_sdnn = _clamp(
            54.0
            - ((heart_rate - 60.0) * 0.35)
            - (physical_effort * 12.0)
            + (walking_steadiness * 5.0)
            + _clamp((sleep_hours - 6.5) * 2.0, -6.0, 8.0),
            *ALS_FEATURE_LIMITS["hrv_sdnn"],
        )
        hrv_pnn50 = _clamp(
            24.0
            - ((heart_rate - 60.0) * 0.18)
            - (physical_effort * 10.0)
            + (walking_steadiness * 8.0)
            + _clamp((sleep_hours - 7.0) * 3.0, -10.0, 10.0),
            *ALS_FEATURE_LIMITS["hrv_pnn50"],
        )

        motion_intensity = (
            (walking_speed * 0.35)
            + (physical_effort * 1.2)
            + (stair_speed * 0.4)
            + min(0.5, (stairs_up + stairs_down) * 0.03)
        )

        derived_rows.append(
            {
                "hrv_rmssd": float(hrv_rmssd),
                "hrv_sdnn": float(hrv_sdnn),
                "hrv_pnn50": float(hrv_pnn50),
                "hr_mean": float(_clamp(mean(trailing_hr), *ALS_FEATURE_LIMITS["hr_mean"])),
                "hr_variance": float(
                    _clamp(_variance(trailing_hr), *ALS_FEATURE_LIMITS["hr_variance"])
                ),
                "skin_temp_delta": float(
                    _clamp(skin_temp_delta, *ALS_FEATURE_LIMITS["skin_temp_delta"])
                ),
                "ambient_noise_db": float(
                    _clamp(ambient_noise_db, *ALS_FEATURE_LIMITS["ambient_noise_db"])
                ),
                "accel_intensity_mean": float(
                    _clamp(motion_intensity, *ALS_FEATURE_LIMITS["accel_intensity_mean"])
                ),
            }
        )

    return derived_rows
