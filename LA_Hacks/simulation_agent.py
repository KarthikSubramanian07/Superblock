from uagents import Agent, Context, Protocol, Model
from pydantic import BaseModel, Field
from typing import List, Dict
import requests
from config import AGENT_SEEDS, AGENT_PORTS, ASI_ONE_API_KEY, ASI_ONE_ENDPOINT, MODEL

class DiagnosisResult(BaseModel):
    failure_modes: List[dict]
    root_causes: List[str]
    recommendations: List[str]
    confidence: float

class SimulationScenario(BaseModel):
    scenario_name: str = Field(description="Name of the intervention scenario")
    description: str = Field(description="Detailed description of the intervention")
    predicted_als_reduction: float = Field(description="Predicted ALS reduction in %")
    implementation_cost: float = Field(description="Estimated implementation cost")
    time_to_implement: str = Field(description="Estimated implementation time")
    confidence: float = Field(description="Confidence in prediction")

class SimulationRequest(BaseModel):
    diagnosis: DiagnosisResult = Field(description="Diagnosis results to simulate interventions")

simulation_agent = Agent(
    name="simulation_agent",
    seed=AGENT_SEEDS["simulation"],
    port=AGENT_PORTS["simulation"],
    endpoint=[f"http://127.0.0.1:{AGENT_PORTS['simulation']}/submit"]
)

simulation_proto = Protocol("simulation")

@simulation_proto.on_message(model=SimulationRequest)
async def handle_simulation(ctx: Context, sender: str, msg: SimulationRequest):
    """Run counterfactual What-If simulations"""
    failure_modes = msg.diagnosis.failure_modes
    
    # Generate intervention scenarios
    scenarios = generate_intervention_scenarios(failure_modes)
    
    # Run simulations using ASI:One
    simulated_results = []
    for scenario in scenarios:
        result = simulate_scenario(scenario, failure_modes)
        simulated_results.append(result)
    
    ctx.logger.info(f"Simulation complete: {len(simulated_results)} scenarios evaluated")

def generate_intervention_scenarios(failure_modes: List[dict]) -> List[dict]:
    """Generate potential intervention scenarios"""
    scenarios = [
        {
            "name": "Shade Canopy Installation",
            "description": "Install solar-powered shade structures in high-heat areas",
            "type": "infrastructure",
            "target_zones": ["zone_1", "zone_2"]
        },
        {
            "name": "Urban Parklets",
            "description": "Convert parking spaces to green parklets with vegetation",
            "type": "green_infrastructure",
            "target_zones": ["zone_1", "zone_3"]
        },
        {
            "name": "Cool Roof Program",
            "description": "Retrofit buildings with reflective roofing materials",
            "type": "building_retrofit",
            "target_zones": ["zone_2", "zone_4"]
        },
        {
            "name": "Vertical Gardens",
            "description": "Install green walls on buildings to reduce heat absorption",
            "type": "vegetation",
            "target_zones": ["zone_1", "zone_2", "zone_3"]
        }
    ]
    return scenarios

def simulate_scenario(scenario: dict, failure_modes: List[dict]) -> SimulationScenario:
    """Simulate the impact of an intervention scenario"""
    simulation_prompt = f"""
    Simulate the impact of this urban heat intervention:
    
    Scenario: {scenario['name']}
    Description: {scenario['description']}
    Target Zones: {scenario['target_zones']}
    
    Current Failure Modes:
    {failure_modes}
    
    Estimate:
    1. Predicted ALS (Average Land Surface) temperature reduction in percentage
    2. Implementation cost on a scale of 1-10 (1=cheap, 10=expensive)
    3. Time to implement (immediate, short-term, long-term)
    4. Overall confidence in predictions (0-1)
    
    Provide specific numerical estimates.
    """
    
    try:
        asi_response = query_asi_one(simulation_prompt)
        return parse_simulation_response(scenario, asi_response)
    except Exception as e:
        print(f"Simulation error: {e}")
        return SimulationScenario(
            scenario_name=scenario["name"],
            description=scenario["description"],
            predicted_als_reduction=0.0,
            implementation_cost=0.0,
            time_to_implement="unknown",
            confidence=0.0
        )

def query_asi_one(prompt: str) -> str:
    """Query ASI:One for simulation analysis"""
    headers = {
        "Authorization": f"Bearer {ASI_ONE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are an urban climate simulation expert."},
            {"role": "user", "content": prompt}
        ]
    }
    
    response = requests.post(ASI_ONE_ENDPOINT, headers=headers, json=payload, timeout=10)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

def parse_simulation_response(scenario: dict, response: str) -> SimulationScenario:
    """Parse simulation response into structured data"""
    # Implement parsing logic based on response format
    return SimulationScenario(
        scenario_name=scenario["name"],
        description=scenario["description"],
        predicted_als_reduction=15.5,  # Example value
        implementation_cost=7.0,  # Example value
        time_to_implement="short-term",
        confidence=0.78
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
