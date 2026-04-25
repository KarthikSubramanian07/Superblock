from __future__ import annotations

import asyncio
import hashlib
import importlib.util
import sys
from functools import lru_cache
from pathlib import Path

from app.agent_integration import (
    build_diagnosis_alert_for_hotspot,
    infer_gait_quality,
    infer_heat_flag,
    movement_context_for_agent,
    noise_bucket_from_db,
)
from app.edge_pipeline import build_agent_hotspots
from app.settings import get_settings


def _resolve_agent_system_dir() -> Path:
    settings = get_settings()
    candidates = []
    if settings.agent_system_dir is not None:
        candidates.append(settings.agent_system_dir)
    candidates.extend(
        [
            settings.base_dir / "superblock_repo" / "LA_Hacks",
            settings.base_dir / "LA_Hacks",
            settings.base_dir.parent,
        ]
    )
    for candidate in candidates:
        if (candidate / "ingestion_agent.py").exists():
            return candidate.resolve()
    raise FileNotFoundError("Could not locate LA_Hacks agent system directory.")


@lru_cache(maxsize=None)
def _load_agent_module(module_name: str):
    agent_dir = _resolve_agent_system_dir()
    module_path = agent_dir / f"{module_name}.py"
    if not module_path.exists():
        raise FileNotFoundError(f"Missing agent module: {module_path}")

    if str(agent_dir) not in sys.path:
        sys.path.insert(0, str(agent_dir))

    try:
        asyncio.get_event_loop_policy().get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    spec = importlib.util.spec_from_file_location(f"live_agents.{module_name}", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module spec for {module_name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _build_ingestion_packet(edge_packet: dict[str, object]) -> dict[str, object]:
    user_id = str(edge_packet.get("user_id", "demo_user"))
    token_suffix = hashlib.md5(user_id.encode("utf-8")).hexdigest()[:16]
    context = movement_context_for_agent(str(edge_packet["context"]))
    noise_db = float(edge_packet.get("noise_db", 0.0))
    als_score = float(edge_packet["als_score"])
    return {
        "als_score": als_score,
        "movement_context": context,
        "h3_index": str(edge_packet["h3_index"]),
        "noise_bucket": noise_bucket_from_db(noise_db),
        "heat_flag": infer_heat_flag(als_score, noise_db),
        "gait_quality": infer_gait_quality(str(edge_packet["context"]), als_score),
        "device_token": f"PoH-{token_suffix}",
        "timestamp": str(edge_packet["timestamp"]),
    }


def _offline_narrative_from_plan(
    selected_h3_index: str,
    diagnosis_result: dict[str, object],
    ranked_plan: dict[str, object],
) -> str:
    top = None
    ranked = ranked_plan.get("ranked_interventions")
    if isinstance(ranked, list) and ranked:
        top = ranked[0]

    failure_mode = str(diagnosis_result.get("failure_mode", "Unknown"))
    severity = str(diagnosis_result.get("severity", "unknown"))
    expected_impact = str(ranked_plan.get("expected_impact", "No impact estimate available."))
    recommendation = (
        f"Start with {top.get('scenario_name', 'the top-ranked intervention')} "
        f"at estimated cost {top.get('implementation_cost', 'n/a')}."
        if isinstance(top, dict)
        else "No intervention recommendation is available yet."
    )

    return (
        f"Executive summary: Tile {selected_h3_index} is currently classified as "
        f"{failure_mode} with {severity} severity.\n\n"
        f"Technical analysis: {expected_impact}\n\n"
        f"Recommendations: {recommendation}\n\n"
        f"Next steps: Validate the tile with the live map, then monitor ALS and context "
        f"after the first intervention rollout."
    )


def run_live_agent_workflow(
    packets: list[dict[str, object]],
    h3_index: str | None = None,
) -> dict[str, object] | None:
    hotspots = build_agent_hotspots(packets, limit=20)
    if not hotspots:
        return None

    selected = hotspots[0] if h3_index is None else next(
        (hotspot for hotspot in hotspots if str(hotspot["h3_index"]) == h3_index),
        None,
    )
    if selected is None:
        return None

    selected_h3_index = str(selected["h3_index"])
    tile_packets = [packet for packet in packets if str(packet["h3_index"]) == selected_h3_index][-10:]
    if not tile_packets:
        return None

    ingestion_module = _load_agent_module("ingestion_agent")
    mapping_module = _load_agent_module("mapping_agent")
    diagnosis_module = _load_agent_module("diagnosis_agent")
    simulation_module = _load_agent_module("simulation_agent")
    planner_module = _load_agent_module("planner_agent")
    narrator_module = _load_agent_module("narrator_agent")

    if hasattr(simulation_module, "query_asi_one"):
        simulation_module.query_asi_one = lambda prompt: "offline-simulation"
    # Reset the mapping module's in-memory twin for deterministic runs.
    if hasattr(mapping_module, "tile_windows"):
        mapping_module.tile_windows.clear()
    if hasattr(mapping_module, "red_zone_since"):
        mapping_module.red_zone_since.clear()
    if hasattr(mapping_module, "red_zone_alerted"):
        mapping_module.red_zone_alerted.clear()

    ingestion_results = []
    mapping_results = []
    for edge_packet in tile_packets:
        raw_packet = _build_ingestion_packet(edge_packet)
        ingestion_result = ingestion_module.run_ingestion_request(raw_packet)
        ingestion_results.append(ingestion_result)
        validated_packet = ingestion_result.get("validated_packet")
        if validated_packet:
            mapping_results.append(mapping_module.run_mapping_request(validated_packet))

    if not mapping_results:
        return None

    diagnosis_alert = build_diagnosis_alert_for_hotspot(packets, selected_h3_index)
    if diagnosis_alert is None:
        return None

    diagnosis_result = diagnosis_module.run_diagnosis_request(diagnosis_alert)
    simulation_request = {
        "diagnosis": {
            "failure_modes": [
                {
                    "name": diagnosis_result["failure_mode"],
                    "severity": diagnosis_result["severity"],
                    "confidence": diagnosis_result["confidence"],
                    "evidence": diagnosis_result["signal_evidence"],
                }
            ],
            "root_causes": diagnosis_result["root_causes"],
            "recommendations": diagnosis_result["recommendations"],
            "confidence": diagnosis_result["confidence"],
        }
    }
    simulation_scenarios = simulation_module.run_simulation_request(simulation_request)
    planning_request = {"scenarios": simulation_scenarios}
    ranked_plan = planner_module.run_planning_request(planning_request)
    if hasattr(narrator_module, "query_asi_one"):
        narrator_module.query_asi_one = lambda prompt: _offline_narrative_from_plan(
            selected_h3_index,
            diagnosis_result,
            ranked_plan,
        )
    narration_request = {"plan": ranked_plan, "target_audience": "general"}
    narrative_report = narrator_module.run_narration_request(narration_request)

    return {
        "selected_h3_index": selected_h3_index,
        "agent_execution_mode": "live_module_execution",
        "agent_call_order": [
            "ingestion_agent",
            "mapping_agent",
            "diagnosis_agent",
            "simulation_agent",
            "planner_agent",
            "narrator_agent",
        ],
        "ingestion_results": ingestion_results,
        "mapping_results": mapping_results,
        "diagnosis_alert": diagnosis_alert,
        "diagnosis_result": diagnosis_result,
        "simulation_request": simulation_request,
        "simulation_scenarios": simulation_scenarios,
        "planning_request": planning_request,
        "ranked_plan": ranked_plan,
        "narrative_report": narrative_report,
    }
