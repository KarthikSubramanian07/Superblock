import json
import re
from typing import List

import requests
from pydantic import BaseModel, Field
from uagents import Agent, Context, Protocol

from config import AGENT_PORTS, AGENT_SEEDS, ASI_ONE_API_KEY, ASI_ONE_ENDPOINT, MODEL


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
    endpoint=[f"http://127.0.0.1:{AGENT_PORTS['narrator']}/submit"],
)

narrator_proto = Protocol("narration")


@narrator_proto.on_message(model=NarrationRequest)
async def handle_narration(ctx: Context, sender: str, msg: NarrationRequest):
    """Translate the ranked plan into a stakeholder-readable report."""
    narrative = generate_narrative(msg.plan, msg.target_audience)
    report = NarrativeReport(
        executive_summary=narrative["executive_summary"],
        technical_analysis=narrative["technical_analysis"],
        recommendations=narrative["recommendations"],
        next_steps=narrative["next_steps"],
    )
    ctx.logger.info("Narrative report generated successfully")


def _fallback_narrative(plan: RankedPlan, audience: str) -> dict:
    top = plan.ranked_interventions[0] if plan.ranked_interventions else None
    top_name = top.get("scenario_name", "the leading intervention") if top else "the leading intervention"
    top_cost = top.get("implementation_cost", "n/a") if top else "n/a"
    top_brc = top.get("brc", "n/a") if top else "n/a"

    executive_summary = (
        f"For a {audience} audience, the current ranked plan favors {top_name} as the fastest "
        f"high-value intervention. {plan.expected_impact} within an estimated total budget of "
        f"${plan.total_budget:,.0f}."
    )
    technical_analysis = (
        f"The planner ranked {len(plan.ranked_interventions)} interventions using relief-per-cost logic. "
        f"The leading option has an estimated implementation cost of ${top_cost:,.0f} and a BRC of {top_brc}."
    )
    recommendations = (
        f"Start with {top_name}, then sequence the remaining roadmap items in ranked order while validating "
        f"the biometrics trend after each rollout."
        if top
        else "No intervention recommendation is available yet."
    )
    next_steps = (
        "Confirm the selected hotspot on the live dashboard, assign owners for phase one execution, "
        "and compare pre/post ALS metrics after the first intervention window."
    )

    return {
        "executive_summary": executive_summary,
        "technical_analysis": technical_analysis,
        "recommendations": recommendations,
        "next_steps": next_steps,
    }


def generate_narrative(plan: RankedPlan, audience: str) -> dict:
    """Generate human-readable narrative using ASI:One with robust fallback."""
    narrative_prompt = f"""
    Create an urban intervention report for a {audience} audience.

    Ranked interventions:
    {json.dumps(plan.ranked_interventions, indent=2)}

    Total budget: {plan.total_budget}
    Expected impact: {plan.expected_impact}
    Implementation roadmap:
    {json.dumps(plan.implementation_roadmap, indent=2)}

    Return ONLY valid JSON with this exact shape:
    {{
      "executive_summary": "...",
      "technical_analysis": "...",
      "recommendations": "...",
      "next_steps": "..."
    }}
    """

    try:
        asi_response = query_asi_one(narrative_prompt)
        return parse_narrative_response(asi_response, plan, audience)
    except Exception as exc:
        print(f"Narrative generation error: {exc}")
        return _fallback_narrative(plan, audience)


def query_asi_one(prompt: str) -> str:
    """Query ASI:One for narrative generation."""
    headers = {
        "Authorization": f"Bearer {ASI_ONE_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are an expert urban planning communicator."},
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


def parse_narrative_response(response: str, plan: RankedPlan, audience: str) -> dict:
    """Parse narrative response into structured sections."""
    parsed = _extract_json_object(response)
    fallback = _fallback_narrative(plan, audience)
    if parsed:
        sections = {
            "executive_summary": str(parsed.get("executive_summary", fallback["executive_summary"])).strip(),
            "technical_analysis": str(parsed.get("technical_analysis", fallback["technical_analysis"])).strip(),
            "recommendations": str(parsed.get("recommendations", fallback["recommendations"])).strip(),
            "next_steps": str(parsed.get("next_steps", fallback["next_steps"])).strip(),
        }
        if all(sections.values()):
            return sections

    blocks = [block.strip() for block in response.split("\n\n") if block.strip()]
    if len(blocks) >= 4:
        return {
            "executive_summary": blocks[0],
            "technical_analysis": blocks[1],
            "recommendations": blocks[2],
            "next_steps": blocks[3],
        }

    return fallback


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
