from __future__ import annotations

from app.edge_pipeline import build_agent_hotspots, build_hotspot_detail
from app.simulation import INTERVENTION_LIBRARY, simulate_intervention


def noise_bucket_from_db(noise_db: float) -> str:
    if noise_db >= 70.0:
        return "High"
    if noise_db >= 55.0:
        return "Medium"
    return "Low"


def infer_heat_flag(avg_als: float, noise_db: float) -> bool:
    return avg_als >= 0.78 and noise_db >= 65.0


def infer_gait_quality(dominant_context: str, avg_als: float) -> str:
    if dominant_context == "walking" and avg_als >= 0.72:
        return "Degraded"
    return "Good"


def movement_context_for_agent(dominant_context: str) -> str:
    return {
        "stationary": "Stationary",
        "walking": "Walking",
        "transit_like": "Transit",
    }.get(dominant_context, "Stationary")


def build_red_zone_alerts_for_agents(
    packets: list[dict[str, object]],
    limit: int,
) -> list[dict[str, object]]:
    hotspots = build_agent_hotspots(packets, limit=limit)
    alerts: list[dict[str, object]] = []
    for hotspot in hotspots:
        if hotspot["status"] != "red_zone":
            continue
        context_counts = hotspot["context_counts"]
        total = max(int(hotspot["packet_count"]), 1)
        context_distribution = {
            "Stationary": round(context_counts.get("stationary", 0) / total, 3),
            "Walking": round(context_counts.get("walking", 0) / total, 3),
            "Transit": round(context_counts.get("transit_like", 0) / total, 3),
        }
        alerts.append(
            {
                "h3_index": hotspot["h3_index"],
                "avg_als": hotspot["avg_als"],
                "sample_count": hotspot["packet_count"],
                "context_distribution": context_distribution,
                "noise_bucket": noise_bucket_from_db(float(hotspot["noise_db"])),
                "heat_flag": infer_heat_flag(float(hotspot["avg_als"]), float(hotspot["noise_db"])),
                "gait_quality": infer_gait_quality(
                    str(hotspot["dominant_context"]),
                    float(hotspot["avg_als"]),
                ),
                "duration_minutes": float(max(5, hotspot["packet_count"])),
            }
        )
    return alerts


def build_simulation_request_for_agent(
    packets: list[dict[str, object]],
    h3_index: str,
) -> dict[str, object] | None:
    hotspot = build_hotspot_detail(packets, h3_index)
    if hotspot is None:
        return None

    failure_mode = {
        "name": "Acoustic Failure" if float(hotspot["noise_db"]) >= 70.0 else "Infrastructure Friction",
        "severity": "high" if float(hotspot["avg_als"]) >= 0.75 else "moderate",
        "confidence": 0.78,
        "evidence": {
            "avg_als": hotspot["avg_als"],
            "dominant_context": movement_context_for_agent(str(hotspot["dominant_context"])),
            "noise_bucket": noise_bucket_from_db(float(hotspot["noise_db"])),
            "packet_count": hotspot["packet_count"],
        },
    }

    root_causes = [
        "Sustained elevated autonomic load in the selected tile.",
        f"Dominant context is {hotspot['dominant_context']} with noise at {hotspot['noise_db']} dB.",
    ]
    recommendations = [
        "Evaluate shade and pedestrian comfort interventions first.",
        "Prioritize lower-cost fixes before capital-heavy construction.",
    ]

    return {
        "diagnosis": {
            "failure_modes": [failure_mode],
            "root_causes": root_causes,
            "recommendations": recommendations,
            "confidence": 0.78,
        }
    }


def build_planning_request_for_agent(
    packets: list[dict[str, object]],
    h3_index: str,
) -> dict[str, object] | None:
    hotspot = build_hotspot_detail(packets, h3_index)
    if hotspot is None:
        return None

    scenarios: list[dict[str, object]] = []
    for intervention_type in INTERVENTION_LIBRARY:
        simulation = simulate_intervention(
            packets,
            h3_index=h3_index,
            intervention_type=intervention_type,
            intensity=1.0,
            budget_usd=0.0,
        )
        if simulation is None:
            continue
        scenarios.append(
            {
                "scenario_name": intervention_type,
                "description": f"Simulated {intervention_type} for hotspot {h3_index}.",
                "predicted_als_reduction": round(
                    float(simulation["estimated_als_reduction"]) * 100.0,
                    2,
                ),
                "implementation_cost": float(simulation["estimated_cost_usd"]),
                "time_to_implement": (
                    "immediate"
                    if intervention_type == "longer_crossing_time"
                    else "short-term"
                    if intervention_type in {"shade_canopy", "parklet"}
                    else "long-term"
                ),
                "confidence": 0.76,
            }
        )

    return {"scenarios": scenarios}
