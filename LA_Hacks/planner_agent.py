from uagents import Agent, Context, Protocol, Model
from pydantic import BaseModel, Field
from typing import List
from config import AGENT_SEEDS, AGENT_PORTS, AGENT_ADDRESSES

class SimulationScenario(BaseModel):
    scenario_name: str
    description: str
    predicted_als_reduction: float
    implementation_cost: float
    time_to_implement: str
    confidence: float

class RankedPlan(BaseModel):
    ranked_interventions: List[dict] = Field(description="Interventions ranked by Biological Relief Coefficient")
    total_budget: float = Field(description="Total estimated budget")
    expected_impact: str = Field(description="Expected overall impact")
    implementation_roadmap: List[dict] = Field(description="Step-by-step implementation plan")

class PlanningRequest(BaseModel):
    scenarios: List[SimulationScenario] = Field(description="Simulation scenarios to rank")

planner_agent = Agent(
    name="planner_agent",
    seed=AGENT_SEEDS["planner"],
    port=AGENT_PORTS["planner"],
    mailbox=True,
    publish_agent_details=True,
)

planner_proto = Protocol("planning")

@planner_proto.on_message(model=PlanningRequest)
async def handle_planning(ctx: Context, sender: str, msg: PlanningRequest):
    """Rank interventions by Biological Relief Coefficient"""
    scenarios = msg.scenarios
    
    # Calculate Biological Relief Coefficient for each scenario
    ranked_scenarios = rank_by_brc(scenarios)
    
    # Create implementation roadmap
    roadmap = create_implementation_roadmap(ranked_scenarios)
    
    plan = RankedPlan(
        ranked_interventions=ranked_scenarios,
        total_budget=sum(s["implementation_cost"] for s in ranked_scenarios[:3]),
        expected_impact=f"Expected {ranked_scenarios[0]['als_reduction']}% ALS reduction",
        implementation_roadmap=roadmap
    )
    
    ctx.logger.info(f"Planning complete: {len(ranked_scenarios)} interventions ranked")

def rank_by_brc(scenarios: List[SimulationScenario]) -> List[dict]:
    """Rank scenarios by Biological Relief Coefficient (ALS reduction / cost)"""
    scored_scenarios = []
    
    for scenario in scenarios:
        # Calculate BRC: ALS reduction per unit cost
        if scenario.implementation_cost > 0:
            brc = scenario.predicted_als_reduction / scenario.implementation_cost
        else:
            brc = 0
        
        scored_scenarios.append({
            "scenario_name": scenario.scenario_name,
            "description": scenario.description,
            "als_reduction": scenario.predicted_als_reduction,
            "implementation_cost": scenario.implementation_cost,
            "time_to_implement": scenario.time_to_implement,
            "brc": brc,
            "confidence": scenario.confidence
        })
    
    # Sort by BRC (descending)
    ranked = sorted(scored_scenarios, key=lambda x: x["brc"], reverse=True)
    return ranked

def create_implementation_roadmap(ranked_scenarios: List[dict]) -> List[dict]:
    """Create step-by-step implementation plan"""
    roadmap = []
    
    # Phase 1: Quick wins (high BRC, short implementation time)
    quick_wins = [s for s in ranked_scenarios if s["time_to_implement"] == "immediate"]
    for i, scenario in enumerate(quick_wins[:2]):
        roadmap.append({
            "phase": 1,
            "step": i + 1,
            "intervention": scenario["scenario_name"],
            "timeline": "Week 1-2",
            "priority": "high"
        })
    
    # Phase 2: Medium-term projects
    medium_term = [s for s in ranked_scenarios if s["time_to_implement"] == "short-term"]
    for i, scenario in enumerate(medium_term[:2]):
        roadmap.append({
            "phase": 2,
            "step": i + 1,
            "intervention": scenario["scenario_name"],
            "timeline": "Month 1-3",
            "priority": "medium"
        })
    
    # Phase 3: Long-term strategic projects
    long_term = [s for s in ranked_scenarios if s["time_to_implement"] == "long-term"]
    for i, scenario in enumerate(long_term[:1]):
        roadmap.append({
            "phase": 3,
            "step": i + 1,
            "intervention": scenario["scenario_name"],
            "timeline": "Month 4-12",
            "priority": "strategic"
        })
    
    return roadmap


def run_planning_request(payload: dict) -> dict:
    """Import-safe helper for backend orchestration."""
    request = PlanningRequest(**payload)
    ranked_scenarios = rank_by_brc(request.scenarios)
    roadmap = create_implementation_roadmap(ranked_scenarios)
    plan = RankedPlan(
        ranked_interventions=ranked_scenarios,
        total_budget=sum(s["implementation_cost"] for s in ranked_scenarios[:3]),
        expected_impact=(
            f"Expected {ranked_scenarios[0]['als_reduction']}% ALS reduction"
            if ranked_scenarios else "No impact estimate available"
        ),
        implementation_roadmap=roadmap,
    )
    return plan.model_dump()

planner_agent.include(planner_proto, publish_manifest=True)

if __name__ == "__main__":
    planner_agent.run()
