import json
import re
from typing import Dict, List

import requests
from pydantic import BaseModel, Field
from uagents import Agent, Context, Protocol

from config import AGENT_PORTS, AGENT_SEEDS, ASI_ONE_API_KEY, ASI_ONE_ENDPOINT, MODEL


class DiagnosisResult(BaseModel):
    failure_modes: List[dict]
    root_causes: List[str]
    recommendations: List[str]
    confidence: float


class SimulationScenario(BaseModel):
    scenario_name: str = Field(description="Name of the intervention scenario")
    description: str = Field(description="Detailed description of the intervention")
    predicted_als_reduction: float = Field(description="Predicted ALS reduction in %")
    implementation_cost: float = Field(description="Estimated implementation cost in USD")
    time_to_implement: str = Field(description="Estimated implementation time")
    confidence: float = Field(description="Confidence in prediction")


class SimulationRequest(BaseModel):
    diagnosis: DiagnosisResult = Field(description="Diagnosis results to simulate interventions")


simulation_agent = Agent(
    name="simulation_agent",
    seed=AGENT_SEEDS["simulation"],
    port=AGENT_PORTS["simulation"],
    endpoint=[f"http://127.0.0.1:{AGENT_PORTS['simulation']}/submit"],
)

simulation_proto = Protocol("simulation")


SCENARIO_LIBRARY: List[dict] = [
    {
        "name": "Shade Canopy Installation",
        "description": "Install solar-powered shade structures in high-heat pedestrian corridors.",
        "type": "shade",
        "base_reduction": 12.0,
        "base_cost": 18000.0,
        "time": "short-term",
    },
    {
        "name": "Urban Parklets",
        "description": "Convert curbside spaces into small green recovery zones with seating and planting.",
        "type": "green_infrastructure",
        "base_reduction": 10.5,
        "base_cost": 22000.0,
        "time": "short-term",
    },
    {
        "name": "Cool Roof Program",
        "description": "Retrofit nearby roofs with reflective materials to reduce stored heat load.",
        "type": "building_retrofit",
        "base_reduction": 8.5,
        "base_cost": 40000.0,
        "time": "long-term",
    },
    {
        "name": "Vertical Gardens",
        "description": "Install green walls to buffer heat and soften street-level environmental load.",
        "type": "vegetation",
        "base_reduction": 9.0,
        "base_cost": 26000.0,
        "time": "short-term",
    },
]

FAILURE_MODE_EFFECTS: Dict[str, Dict[str, float]] = {
    "Acoustic Failure": {
        "shade": 0.9,
        "green_infrastructure": 1.0,
        "building_retrofit": 0.7,
        "vegetation": 1.15,
    },
    "Heat Exhaustion Onset": {
        "shade": 1.3,
        "green_infrastructure": 1.1,
        "building_retrofit": 1.0,
        "vegetation": 1.15,
    },
    "Air Quality / Crowding Stress": {
        "shade": 0.85,
        "green_infrastructure": 0.95,
        "building_retrofit": 0.8,
        "vegetation": 1.05,
    },
    "Infrastructure Friction": {
        "shade": 0.75,
        "green_infrastructure": 1.05,
        "building_retrofit": 0.6,
        "vegetation": 0.8,
    },
    "Composite Failure": {
        "shade": 1.1,
        "green_infrastructure": 1.05,
        "building_retrofit": 0.9,
        "vegetation": 1.0,
    },
    "Normal": {
        "shade": 0.35,
        "green_infrastructure": 0.35,
        "building_retrofit": 0.25,
        "vegetation": 0.3,
    },
}


@simulation_proto.on_message(model=SimulationRequest)
async def handle_simulation(ctx: Context, sender: str, msg: SimulationRequest):
    """Run counterfactual What-If simulations."""
    failure_modes = msg.diagnosis.failure_modes
    scenarios = generate_intervention_scenarios(failure_modes)
    simulated_results = [simulate_scenario(scenario, failure_modes) for scenario in scenarios]
    ctx.logger.info(f"Simulation complete: {len(simulated_results)} scenarios evaluated")


def generate_intervention_scenarios(failure_modes: List[dict]) -> List[dict]:
    """Generate potential intervention scenarios."""
    dominant_mode = _dominant_failure_mode(failure_modes)
    scenarios = [dict(item) for item in SCENARIO_LIBRARY]

    # Reorder scenarios so the most relevant interventions appear first.
    if dominant_mode == "Heat Exhaustion Onset":
        priority = ["Shade Canopy Installation", "Vertical Gardens", "Urban Parklets", "Cool Roof Program"]
    elif dominant_mode == "Acoustic Failure":
        priority = ["Vertical Gardens", "Urban Parklets", "Shade Canopy Installation", "Cool Roof Program"]
    elif dominant_mode == "Infrastructure Friction":
        priority = ["Urban Parklets", "Shade Canopy Installation", "Vertical Gardens", "Cool Roof Program"]
    else:
        priority = [item["name"] for item in scenarios]

    scenarios.sort(key=lambda item: priority.index(item["name"]) if item["name"] in priority else len(priority))
    return scenarios


def _dominant_failure_mode(failure_modes: List[dict]) -> str:
    if not failure_modes:
        return "Composite Failure"
    ranked = sorted(
        failure_modes,
        key=lambda item: (
            float(item.get("confidence", 0.0)),
            {"critical": 4, "high": 3, "moderate": 2, "low": 1}.get(str(item.get("severity", "low")), 0),
        ),
        reverse=True,
    )
    return str(ranked[0].get("name", "Composite Failure"))


def _heuristic_scenario_estimate(scenario: dict, failure_modes: List[dict]) -> SimulationScenario:
    dominant_mode = _dominant_failure_mode(failure_modes)
    dominant = next((item for item in failure_modes if str(item.get("name")) == dominant_mode), failure_modes[0] if failure_modes else {})
    severity = str(dominant.get("severity", "moderate"))
    confidence = float(dominant.get("confidence", 0.65))
    severity_factor = {
        "low": 0.65,
        "moderate": 1.0,
        "high": 1.2,
        "critical": 1.35,
    }.get(severity, 1.0)
    mode_factor = FAILURE_MODE_EFFECTS.get(dominant_mode, FAILURE_MODE_EFFECTS["Composite Failure"]).get(
        str(scenario["type"]),
        1.0,
    )

    reduction = round(min(35.0, scenario["base_reduction"] * severity_factor * mode_factor), 2)
    cost = round(scenario["base_cost"] * (1.05 if severity in {"high", "critical"} else 1.0), 2)
    adjusted_confidence = round(max(0.45, min(0.94, confidence * 0.92)), 2)

    if dominant_mode == "Normal":
        reduction = round(reduction * 0.45, 2)
        adjusted_confidence = round(min(adjusted_confidence, 0.62), 2)

    return SimulationScenario(
        scenario_name=scenario["name"],
        description=scenario["description"],
        predicted_als_reduction=reduction,
        implementation_cost=cost,
        time_to_implement=scenario["time"],
        confidence=adjusted_confidence,
    )


def simulate_scenario(scenario: dict, failure_modes: List[dict]) -> SimulationScenario:
    """Simulate the impact of an intervention scenario."""
    simulation_prompt = f"""
    You are simulating an urban intervention for a biometric city dashboard.

    Scenario:
    - name: {scenario['name']}
    - description: {scenario['description']}
    - type: {scenario['type']}

    Failure modes:
    {json.dumps(failure_modes, indent=2)}

    Return ONLY valid JSON with this exact shape:
    {{
      "predicted_als_reduction": <number between 0 and 35>,
      "implementation_cost": <number in USD>,
      "time_to_implement": "immediate" | "short-term" | "long-term",
      "confidence": <number between 0 and 1>
    }}
    """

    try:
        asi_response = query_asi_one(simulation_prompt)
        return parse_simulation_response(scenario, failure_modes, asi_response)
    except Exception as exc:
        print(f"Simulation error: {exc}")
        return _heuristic_scenario_estimate(scenario, failure_modes)


def query_asi_one(prompt: str) -> str:
    """Query ASI:One for simulation analysis."""
    headers = {
        "Authorization": f"Bearer {ASI_ONE_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are an urban climate simulation expert."},
            {"role": "user", "content": prompt},
        ],
    }
    response = requests.post(ASI_ONE_ENDPOINT, headers=headers, json=payload, timeout=10)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def _extract_json_object(response: str) -> dict | None:
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", response, flags=re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None


def parse_simulation_response(
    scenario: dict,
    failure_modes: List[dict],
    response: str,
) -> SimulationScenario:
    """Parse simulation response into structured data with heuristic fallback."""
    parsed = _extract_json_object(response)
    fallback = _heuristic_scenario_estimate(scenario, failure_modes)

    if not parsed:
        return fallback

    try:
        predicted_als_reduction = float(parsed.get("predicted_als_reduction", fallback.predicted_als_reduction))
        implementation_cost = float(parsed.get("implementation_cost", fallback.implementation_cost))
        time_to_implement = str(parsed.get("time_to_implement", fallback.time_to_implement))
        confidence = float(parsed.get("confidence", fallback.confidence))
    except (TypeError, ValueError):
        return fallback

    predicted_als_reduction = round(max(0.0, min(35.0, predicted_als_reduction)), 2)
    implementation_cost = round(max(500.0, implementation_cost), 2)
    if time_to_implement not in {"immediate", "short-term", "long-term"}:
        time_to_implement = fallback.time_to_implement
    confidence = round(max(0.0, min(1.0, confidence)), 2)

    return SimulationScenario(
        scenario_name=scenario["name"],
        description=scenario["description"],
        predicted_als_reduction=predicted_als_reduction,
        implementation_cost=implementation_cost,
        time_to_implement=time_to_implement,
        confidence=confidence,
    )


def run_simulation_request(payload: dict) -> List[dict]:
    """Import-safe helper for backend orchestration."""
    request = SimulationRequest(**payload)
    scenarios = generate_intervention_scenarios(request.diagnosis.failure_modes)
    results = [simulate_scenario(scenario, request.diagnosis.failure_modes) for scenario in scenarios]
    return [result.model_dump() for result in results]


if __name__ == "__main__":
    simulation_agent.include(simulation_proto, publish_manifest=True)
    simulation_agent.run()
