"""
HTTP gateway for the Urban Nervous System.

Bridges the Vite UI (`superblock-ui/`) to the live multi-agent stack. The UI
calls `localhost:8000` for tiles / hotspots / diagnosis / simulate / planner —
this gateway serves those endpoints by calling the agents' import-safe
`run_*_request` helpers (sync, in-process). Response shapes mirror
`mockagent/server.js` so the UI's LIVE-mode toggle is drop-in.

Run alongside the Bureau:

    # terminal 1
    python orchestrator.py

    # terminal 2
    uvicorn gateway:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import GATEWAY_PORT
from diagnosis_agent import (
    RedZoneAlert as DiagnosisRedZoneAlert,
    run_diagnosis_request,
)
from ingestion_agent import run_ingestion_request
from mapping_agent import run_mapping_request
from planner_agent import run_planning_request
from simulation_agent import run_simulation_request

# ─── Mock data fallback (parity with mockagent/server.js) ────────────────────
MOCK_DATA_PATH = Path(__file__).parent.parent / "superblock-ui" / "src" / "data" / "mockData.json"
try:
    MOCK_DATA: Dict[str, Any] = json.loads(MOCK_DATA_PATH.read_text())
except FileNotFoundError:
    MOCK_DATA = {"timeframes": [], "hotspots": [], "agents": [], "interventions": []}

STRESSOR_LABELS = {
    "heat_exposure": "Heat exposure",
    "noise_pollution": "Noise pollution",
    "pedestrian_crowding": "Pedestrian crowding",
    "air_quality": "Air quality",
    "transit_delay": "Transit delay",
}

# ─── App ────────────────────────────────────────────────────────────────────
app = FastAPI(title="Urban Nervous System Gateway")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Schemas ────────────────────────────────────────────────────────────────
class SimulateBody(BaseModel):
    h3_index: str
    intervention_id: str
    als_before: float


# ─── Endpoints (mockagent contract parity) ──────────────────────────────────
@app.get("/health")
def health() -> str:
    return "OK"


@app.get("/tiles")
def tiles(hour: int = Query(6, ge=0, le=23)) -> List[Dict[str, Any]]:
    timeframe = next(
        (t for t in MOCK_DATA.get("timeframes", []) if t.get("time_index") == hour),
        None,
    )
    return timeframe.get("tiles", []) if timeframe else []


@app.get("/hotspots")
def hotspots() -> List[Dict[str, Any]]:
    return MOCK_DATA.get("hotspots", [])


@app.get("/agents")
def agents() -> List[Dict[str, Any]]:
    return MOCK_DATA.get("agents", [])


@app.get("/ingestion/status")
def ingestion_status() -> Dict[str, Any]:
    return {
        "packets_per_min": 47,
        "sensors_online": 12,
        "last_batch_id": 128,
        "total_tiles": len(MOCK_DATA.get("timeframes", [{}])[0].get("tiles", [])),
        "status": "active",
    }


def _hotspot_to_redzone(hotspot: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Map the UI's hotspot record into a RedZoneAlert payload for diagnosis_agent."""
    if not hotspot:
        return None
    als = float(hotspot.get("als_score", 0.5))
    severity = hotspot.get("severity", "medium")
    stressors: List[str] = hotspot.get("stressors", [])
    noise = "High" if "noise_pollution" in stressors else "Medium" if "transit_delay" in stressors else "Low"
    heat_flag = "heat_exposure" in stressors
    crowd = "pedestrian_crowding" in stressors
    return {
        "h3_index": hotspot["h3_index"],
        "avg_als": als,
        "sample_count": 30,
        "context_distribution": {
            "Stationary": 0.25 if not crowd else 0.55,
            "Walking": 0.55 if not crowd else 0.30,
            "Transit": 0.20 if not crowd else 0.15,
        },
        "noise_bucket": noise,
        "heat_flag": heat_flag,
        "gait_quality": "Degraded" if severity == "high" else "Good",
        "duration_minutes": 7.0,
    }


@app.get("/diagnosis")
def diagnosis(h3_index: str) -> Dict[str, Any]:
    if not h3_index:
        raise HTTPException(status_code=400, detail="h3_index required")

    hotspot = next(
        (h for h in MOCK_DATA.get("hotspots", []) if h.get("h3_index") == h3_index),
        None,
    )
    redzone_payload = _hotspot_to_redzone(hotspot) if hotspot else None

    if redzone_payload is None:
        # No matching hotspot — match mockagent's "moderate" fallback.
        return {
            "h3_index": h3_index,
            "summary": "Moderate stress detected — insufficient profile data",
            "primary_stressor": "Urban stress",
            "stressors": ["urban_stress"],
            "als_score": 0.5,
            "severity": "medium",
            "recommended_action": "Collect additional sensor data",
        }

    result = run_diagnosis_request(redzone_payload)
    primary = (hotspot.get("stressors") or ["urban_stress"])[0]
    primary_label = STRESSOR_LABELS.get(primary, primary.replace("_", " ").title())
    severity = hotspot.get("severity", "medium")
    location = hotspot.get("location_label", "the selected zone")
    return {
        "h3_index": h3_index,
        "summary": (
            f"{severity.capitalize()} stress at {location} — {primary_label} dominant; "
            f"failure mode: {result['failure_mode']}"
        ),
        "primary_stressor": primary_label,
        "stressors": hotspot.get("stressors", []),
        "als_score": hotspot.get("als_score", result["avg_als"]),
        "severity": severity,
        "recommended_action": (
            "Priority intervention recommended"
            if hotspot.get("als_score", 0) >= 0.7
            else "Monitor and assess further"
        ),
        "failure_mode": result["failure_mode"],
        "confidence": result["confidence"],
        "root_causes": result["root_causes"],
        "recommendations": result["recommendations"],
        "asi_reasoning": result.get("asi_reasoning"),
    }


@app.get("/planner/interventions")
def planner_interventions() -> List[Dict[str, Any]]:
    interventions = list(MOCK_DATA.get("interventions", []))
    interventions.sort(key=lambda i: i.get("relief_coefficient", 0), reverse=True)
    return interventions


@app.post("/simulate")
def simulate(body: SimulateBody) -> Dict[str, Any]:
    hotspot = next(
        (h for h in MOCK_DATA.get("hotspots", []) if h.get("h3_index") == body.h3_index),
        None,
    )
    intervention = next(
        (i for i in MOCK_DATA.get("interventions", []) if i.get("id") == body.intervention_id),
        None,
    )
    if intervention is None:
        raise HTTPException(status_code=404, detail="Intervention not found")

    before = float(hotspot.get("als_score", body.als_before)) if hotspot else body.als_before
    delta_factor = float(intervention.get("predicted_als_delta", -0.1))
    after = max(0.01, before + delta_factor)
    delta = round(after - before, 2)
    pct = round((abs(delta) / before) * 100) if before > 0 else 0
    return {
        "intervention_id": body.intervention_id,
        "h3_index": body.h3_index,
        "als_before": round(before, 2),
        "als_after": round(after, 2),
        "als_delta": delta,
        "percent_reduction": pct,
    }


@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "service": "Urban Nervous System Gateway",
        "port": GATEWAY_PORT,
        "endpoints": [
            "/health",
            "/tiles?hour=N",
            "/hotspots",
            "/agents",
            "/ingestion/status",
            "/diagnosis?h3_index=X",
            "/planner/interventions",
            "POST /simulate",
        ],
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
