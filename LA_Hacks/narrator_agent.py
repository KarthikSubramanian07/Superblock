from uagents import Agent, Context, Protocol, Model
from pydantic import BaseModel, Field
from typing import List
import requests
from config import AGENT_SEEDS, AGENT_PORTS, ASI_ONE_API_KEY, ASI_ONE_ENDPOINT, MODEL

class RankedPlan(BaseModel):
    ranked_interventions: List[dict]
    total_budget: float
    expected_impact: str
    implementation_roadmap: List[dict]

class NarrativeReport(BaseModel):
    executive_summary: str = Field(description="High-level summary for decision makers")
    technical_analysis: str = Field(description="Detailed technical analysis")
    recommendations: str = Field(description="Actionable recommendations")
    next_steps: str = Field(description="Immediate next steps")

class NarrationRequest(BaseModel):
    plan: RankedPlan = Field(description="Ranked plan to narrate")
    target_audience: str = Field(default="general", description="Target audience for the report")

narrator_agent = Agent(
    name="narrator_agent",
    seed=AGENT_SEEDS["narrator"],
    port=AGENT_PORTS["narrator"],
    endpoint=[f"http://127.0.0.1:{AGENT_PORTS['narrator']}/submit"]
)

narrator_proto = Protocol("narration")

@narrator_proto.on_message(model=NarrationRequest)
async def handle_narration(ctx: Context, sender: str, msg: NarrationRequest):
    """Translate reasoning chain for ASI:One Chat Protocol"""
    plan = msg.plan
    
    # Generate narrative using ASI:One
    narrative = generate_narrative(plan, msg.target_audience)
    
    report = NarrativeReport(
        executive_summary=narrative["executive_summary"],
        technical_analysis=narrative["technical_analysis"],
        recommendations=narrative["recommendations"],
        next_steps=narrative["next_steps"]
    )
    
    ctx.logger.info("Narrative report generated successfully")

def generate_narrative(plan: RankedPlan, audience: str) -> dict:
    """Generate human-readable narrative using ASI:One"""
    narrative_prompt = f"""
    Create a comprehensive urban heat island mitigation report for {audience} audience.
    
    Ranked Interventions:
    {plan.ranked_interventions}
    
    Total Budget: {plan.total_budget}
    Expected Impact: {plan.expected_impact}
    
    Implementation Roadmap:
    {plan.implementation_roadmap}
    
    Generate:
    1. Executive Summary (2-3 paragraphs for decision makers)
    2. Technical Analysis (detailed methodology and findings)
    3. Recommendations (actionable steps with priorities)
    4. Next Steps (immediate actions to take)
    
    Make it clear, compelling, and actionable.
    """
    
    try:
        asi_response = query_asi_one(narrative_prompt)
        return parse_narrative_response(asi_response)
    except Exception as e:
        print(f"Narrative generation error: {e}")
        return {
            "executive_summary": "Error generating narrative",
            "technical_analysis": "",
            "recommendations": "",
            "next_steps": ""
        }

def query_asi_one(prompt: str) -> str:
    """Query ASI:One for narrative generation"""
    headers = {
        "Authorization": f"Bearer {ASI_ONE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are an expert urban planning communicator."},
            {"role": "user", "content": prompt}
        ]
    }
    
    response = requests.post(ASI_ONE_ENDPOINT, headers=headers, json=payload, timeout=10)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

def parse_narrative_response(response: str) -> dict:
    """Parse narrative response into structured sections"""
    # Implement parsing logic based on response format
    sections = response.split("\n\n")
    
    return {
        "executive_summary": sections[0] if len(sections) > 0 else "",
        "technical_analysis": sections[1] if len(sections) > 1 else "",
        "recommendations": sections[2] if len(sections) > 2 else "",
        "next_steps": sections[3] if len(sections) > 3 else ""
    }


def run_narration_request(payload: dict) -> dict:
    """Import-safe helper for backend orchestration."""
    request = NarrationRequest(**payload)
    narrative = generate_narrative(RankedPlan(**request.plan.model_dump()), request.target_audience)
    report = NarrativeReport(
        executive_summary=narrative["executive_summary"],
        technical_analysis=narrative["technical_analysis"],
        recommendations=narrative["recommendations"],
        next_steps=narrative["next_steps"],
    )
    return report.model_dump()

if __name__ == "__main__":
    narrator_agent.include(narrator_proto, publish_manifest=True)
    narrator_agent.run()
