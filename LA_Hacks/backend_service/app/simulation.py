from __future__ import annotations

from app.edge_pipeline import build_hotspot_detail


INTERVENTION_LIBRARY: dict[str, dict[str, float]] = {
    "shade_canopy": {
        "als_reduction": 0.10,
        "noise_reduction_db": 2.0,
        "cost_usd": 12000.0,
    },
    "longer_crossing_time": {
        "als_reduction": 0.07,
        "noise_reduction_db": 0.5,
        "cost_usd": 5000.0,
    },
    "parklet": {
        "als_reduction": 0.12,
        "noise_reduction_db": 3.0,
        "cost_usd": 18000.0,
    },
    "pedestrian_bridge": {
        "als_reduction": 0.18,
        "noise_reduction_db": 4.0,
        "cost_usd": 75000.0,
    },
}


def simulate_intervention(
    packets: list[dict[str, object]],
    *,
    h3_index: str,
    intervention_type: str,
    intensity: float,
    budget_usd: float,
) -> dict[str, object] | None:
    hotspot = build_hotspot_detail(packets, h3_index)
    if hotspot is None:
        return None

    intervention = INTERVENTION_LIBRARY[intervention_type]
    raw_als_reduction = intervention["als_reduction"] * intensity
    raw_noise_reduction = intervention["noise_reduction_db"] * intensity
    estimated_cost = intervention["cost_usd"] * intensity

    budget_factor = 1.0
    assumptions = [
        f"Rule-based estimate using intervention profile for {intervention_type}.",
        "Impact is applied only to the selected hotspot tile in this version.",
    ]
    if budget_usd > 0.0 and estimated_cost > budget_usd:
        budget_factor = budget_usd / estimated_cost
        assumptions.append("Impact scaled down because requested budget is below estimated cost.")

    estimated_als_reduction = min(float(hotspot["avg_als"]), raw_als_reduction * budget_factor)
    estimated_noise_reduction = min(float(hotspot["noise_db"]), raw_noise_reduction * budget_factor)

    after_avg_als = max(0.0, float(hotspot["avg_als"]) - estimated_als_reduction)
    after_noise_db = max(0.0, float(hotspot["noise_db"]) - estimated_noise_reduction)

    before_snapshot = {
        "h3_index": str(hotspot["h3_index"]),
        "avg_als": float(hotspot["avg_als"]),
        "dominant_context": str(hotspot["dominant_context"]),
        "noise_db": float(hotspot["noise_db"]),
        "status": str(hotspot["status"]),
    }
    after_snapshot = {
        "h3_index": str(hotspot["h3_index"]),
        "avg_als": round(after_avg_als, 4),
        "dominant_context": str(hotspot["dominant_context"]),
        "noise_db": round(after_noise_db, 2),
        "status": "red_zone" if after_avg_als >= 0.66 else "blue_zone",
    }

    impact_score = round(
        estimated_als_reduction / max(estimated_cost, 1.0) * 100000.0,
        6,
    )

    return {
        "h3_index": str(hotspot["h3_index"]),
        "intervention_type": intervention_type,
        "budget_usd": float(budget_usd),
        "estimated_cost_usd": round(estimated_cost, 2),
        "estimated_als_reduction": round(estimated_als_reduction, 4),
        "estimated_noise_reduction_db": round(estimated_noise_reduction, 2),
        "impact_score": impact_score,
        "before": before_snapshot,
        "after": after_snapshot,
        "assumptions": assumptions,
    }
