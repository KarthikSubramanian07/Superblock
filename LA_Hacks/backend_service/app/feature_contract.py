from __future__ import annotations

import math
from dataclasses import dataclass

from training.features import expected_feature_names


@dataclass(frozen=True)
class FeatureRule:
    minimum: float | None = None
    maximum: float | None = None
    finite_only: bool = True


COMPONENT_ABS_LIMIT = 100.0
MAGNITUDE_MAX_LIMIT = 200.0


def build_feature_rules() -> dict[str, FeatureRule]:
    rules: dict[str, FeatureRule] = {}
    for feature_name in expected_feature_names():
        if feature_name.endswith(("_std", "_energy", "_sma")):
            rules[feature_name] = FeatureRule(minimum=0.0)
            continue

        if feature_name.startswith("accel_mag_"):
            rules[feature_name] = FeatureRule(minimum=0.0, maximum=MAGNITUDE_MAX_LIMIT)
            continue

        rules[feature_name] = FeatureRule(
            minimum=-COMPONENT_ABS_LIMIT,
            maximum=COMPONENT_ABS_LIMIT,
        )

    return rules


FEATURE_RULES = build_feature_rules()
EXPECTED_FEATURES = tuple(expected_feature_names())
DEFAULT_FEATURE_FILL_VALUE = 0.0


def validate_feature_payload(features: dict[str, float]) -> None:
    extra = [name for name in features if name not in FEATURE_RULES]
    if extra:
        raise ValueError("Unexpected features provided: " + ", ".join(sorted(extra)))

    for feature_name, raw_value in features.items():
        value = float(raw_value)
        if not math.isfinite(value):
            raise ValueError(f"Feature {feature_name} must be finite.")

        rule = FEATURE_RULES[feature_name]
        if rule.minimum is not None and value < rule.minimum:
            raise ValueError(
                f"Feature {feature_name} must be >= {rule.minimum}, got {value}."
            )
        if rule.maximum is not None and value > rule.maximum:
            raise ValueError(
                f"Feature {feature_name} must be <= {rule.maximum}, got {value}."
            )

    _validate_internal_consistency(features)


def complete_feature_payload(features: dict[str, float]) -> dict[str, float]:
    completed = {name: DEFAULT_FEATURE_FILL_VALUE for name in EXPECTED_FEATURES}
    completed.update({name: float(value) for name, value in features.items()})
    return completed


def _validate_internal_consistency(features: dict[str, float]) -> None:
    prefixes = ("accel_x_", "accel_y_", "accel_z_", "accel_mag_")
    for prefix in prefixes:
        required_names = (
            f"{prefix}min",
            f"{prefix}median",
            f"{prefix}max",
            f"{prefix}mean",
        )
        if not all(name in features for name in required_names):
            continue

        min_value = float(features[f"{prefix}min"])
        median_value = float(features[f"{prefix}median"])
        max_value = float(features[f"{prefix}max"])
        mean_value = float(features[f"{prefix}mean"])

        if min_value > max_value:
            raise ValueError(f"Feature pair {prefix}min/{prefix}max is inconsistent.")
        if not (min_value <= median_value <= max_value):
            raise ValueError(
                f"Feature {prefix}median must lie between {prefix}min and {prefix}max."
            )
        if not (min_value <= mean_value <= max_value):
            raise ValueError(
                f"Feature {prefix}mean must lie between {prefix}min and {prefix}max."
            )
