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


def build_diagnosis_alert_for_hotspot(
    packets: list[dict[str, object]],
    h3_index: str,
) -> dict[str, object] | None:
    hotspot = build_hotspot_detail(packets, h3_index)
    if hotspot is None:
        return None

    context_counts = hotspot["context_counts"]
    total = max(int(hotspot["packet_count"]), 1)
    return {
        "h3_index": hotspot["h3_index"],
        "avg_als": hotspot["avg_als"],
        "sample_count": hotspot["packet_count"],
        "context_distribution": {
            "Stationary": round(context_counts.get("stationary", 0) / total, 3),
            "Walking": round(context_counts.get("walking", 0) / total, 3),
            "Transit": round(context_counts.get("transit_like", 0) / total, 3),
        },
        "noise_bucket": noise_bucket_from_db(float(hotspot["noise_db"])),
        "heat_flag": infer_heat_flag(float(hotspot["avg_als"]), float(hotspot["noise_db"])),
        "gait_quality": infer_gait_quality(
            str(hotspot["dominant_context"]),
            float(hotspot["avg_als"]),
        ),
        "duration_minutes": float(max(5, hotspot["packet_count"])),
    }


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


def _rank_scenarios(scenarios: list[dict[str, object]]) -> list[dict[str, object]]:
    ranked: list[dict[str, object]] = []
    for scenario in scenarios:
        cost = max(float(scenario["implementation_cost"]), 1.0)
        reduction = float(scenario["predicted_als_reduction"])
        ranked.append(
            {
                **scenario,
                "brc": round(reduction / cost, 6),
            }
        )
    ranked.sort(key=lambda item: item["brc"], reverse=True)
    return ranked


def _build_implementation_roadmap(ranked_scenarios: list[dict[str, object]]) -> list[dict[str, object]]:
    roadmap: list[dict[str, object]] = []
    for index, scenario in enumerate(ranked_scenarios[:3], start=1):
        roadmap.append(
            {
                "phase": index,
                "intervention": scenario["scenario_name"],
                "timeline": scenario["time_to_implement"],
                "priority": "high" if index == 1 else "medium",
            }
        )
    return roadmap


def build_agent_orchestration_flow(
    packets: list[dict[str, object]],
    h3_index: str | None = None,
) -> dict[str, object] | None:
    hotspots = build_agent_hotspots(packets, limit=1 if h3_index is None else 20)
    selected = None
    if h3_index is None:
        selected = hotspots[0] if hotspots else None
    else:
        for hotspot in hotspots:
            if str(hotspot["h3_index"]) == h3_index:
                selected = hotspot
                break
        if selected is None:
            detail = build_hotspot_detail(packets, h3_index)
            if detail is not None:
                selected = detail

    if selected is None:
        return None

    selected_h3_index = str(selected["h3_index"])
    alerts = build_red_zone_alerts_for_agents(packets, limit=20)
    diagnosis_alert = next(
        (alert for alert in alerts if str(alert["h3_index"]) == selected_h3_index),
        None,
    )
    if diagnosis_alert is None:
        diagnosis_alert = build_diagnosis_alert_for_hotspot(packets, selected_h3_index)
    simulation_request = build_simulation_request_for_agent(packets, selected_h3_index)
    planning_request = build_planning_request_for_agent(packets, selected_h3_index)
    if diagnosis_alert is None or simulation_request is None or planning_request is None:
        return None

    ranked_interventions = _rank_scenarios(planning_request["scenarios"])
    roadmap = _build_implementation_roadmap(ranked_interventions)
    top = ranked_interventions[0] if ranked_interventions else None
    ranked_plan = {
        "ranked_interventions": ranked_interventions,
        "total_budget": round(sum(item["implementation_cost"] for item in ranked_interventions[:3]), 2),
        "expected_impact": (
            f"Expected {top['predicted_als_reduction']}% ALS reduction from {top['scenario_name']}"
            if top
            else "No intervention scenarios available."
        ),
        "implementation_roadmap": roadmap,
    }

    executive_summary = (
        f"Tile {selected_h3_index} is currently a {selected['status']} with avg ALS {selected['avg_als']}. "
        f"The top intervention is {top['scenario_name']}." if top else
        f"Tile {selected_h3_index} requires further analysis."
    )

    return {
        "selected_h3_index": selected_h3_index,
        "diagnosis_alert": diagnosis_alert,
        "simulation_request": simulation_request,
        "planning_request": planning_request,
        "ranked_plan": ranked_plan,
        "narrative_summary": {
            "executive_summary": executive_summary,
            "technical_analysis": (
                f"Dominant context is {selected['dominant_context']} with noise at {selected['noise_db']} dB."
            ),
            "recommendations": (
                top["description"] if top else "Prioritize more data collection."
            ),
            "next_steps": (
                f"Evaluate {top['scenario_name']} first and monitor tile {selected_h3_index} after rollout."
                if top
                else f"Continue monitoring tile {selected_h3_index}."
            ),
        },
    }
