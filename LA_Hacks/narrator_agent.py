from datetime import datetime, timezone
from uuid import uuid4
from uagents import Agent, Context, Protocol, Model
from pydantic import BaseModel, Field
from typing import List, Optional
import requests
from config import AGENT_SEEDS, AGENT_PORTS, AGENT_ADDRESSES, ASI_ONE_API_KEY, ASI_ONE_ENDPOINT, MODEL

try:
    from uagents_core.contrib.protocols.chat import (
        ChatMessage,
        ChatAcknowledgement,
        TextContent,
        EndSessionContent,
        chat_protocol_spec,
    )
    _CHAT_PROTOCOL_AVAILABLE = True
except ImportError:
    _CHAT_PROTOCOL_AVAILABLE = False

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
    mailbox=True,
    publish_agent_details=True,
)

narrator_proto = Protocol("narration")

# Last cached pipeline output — populated by NarrationRequest handler, served via Chat Protocol.
_latest_plan: Optional["RankedPlan"] = None
_latest_report: Optional["NarrativeReport"] = None

@narrator_proto.on_message(model=NarrationRequest)
async def handle_narration(ctx: Context, sender: str, msg: NarrationRequest):
    """Translate reasoning chain for ASI:One Chat Protocol"""
    global _latest_plan, _latest_report
    plan = msg.plan

    narrative = generate_narrative(plan, msg.target_audience)

    report = NarrativeReport(
        executive_summary=narrative["executive_summary"],
        technical_analysis=narrative["technical_analysis"],
        recommendations=narrative["recommendations"],
        next_steps=narrative["next_steps"],
    )
    _latest_plan = plan
    _latest_report = report
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

narrator_agent.include(narrator_proto, publish_manifest=True)


# ─────────────────────────────────────────────────────────────────────────────
# ASI:One Chat Protocol — entry point for ASI:One discoverability
# ─────────────────────────────────────────────────────────────────────────────
def _build_chat_response(question: str) -> str:
    """Synthesize a stakeholder-facing answer from cached pipeline state."""
    plan = _latest_plan
    report = _latest_report

    if plan is None or report is None:
        context_block = (
            "The Urban Nervous System is monitoring Downtown LA. "
            "No Red Zones currently active — all tiles within nominal ALS range."
        )
    else:
        top = plan.ranked_interventions[:3]
        ranked_text = "\n".join(
            f"  {i+1}. {item.get('scenario_name', '?')} — "
            f"ALS reduction {item.get('als_reduction', 0):.1f}%, "
            f"cost {item.get('implementation_cost', 0):.0f}, "
            f"BRC {item.get('brc', 0):.2f}"
            for i, item in enumerate(top)
        )
        context_block = (
            f"Latest planner output (ranked by Biological Relief Coefficient):\n{ranked_text}\n\n"
            f"Total budget: {plan.total_budget:.0f}\n"
            f"Expected impact: {plan.expected_impact}\n\n"
            f"Executive summary: {report.executive_summary}\n"
        )

    prompt = (
        f"You are the Narrator Agent for the Urban Nervous System — a multi-agent "
        f"system that turns Apple Watch biometric stress signals into ranked city-planning "
        f"interventions. A stakeholder asked: \"{question}\"\n\n"
        f"Context from the pipeline:\n{context_block}\n\n"
        f"Answer in 2–4 paragraphs. Be specific about which intervention you recommend, "
        f"the predicted ALS reduction, and the cost. Cite the Biological Relief Coefficient "
        f"when ranking. End with a clear next-step call to action."
    )

    try:
        response = requests.post(
            ASI_ONE_ENDPOINT,
            headers={
                "Authorization": f"Bearer {ASI_ONE_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a planner-facing communicator. Translate multi-agent "
                            "biometric stress analysis into clear, evidence-backed "
                            "recommendations for city stakeholders."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 600,
            },
            timeout=15,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return (
            f"[Narrator Agent — ASI:One unavailable: {e}]\n\n"
            f"Fallback summary based on cached pipeline state:\n{context_block}"
        )


if _CHAT_PROTOCOL_AVAILABLE:
    chat_proto = Protocol(spec=chat_protocol_spec)

    @chat_proto.on_message(model=ChatMessage)
    async def handle_chat(ctx: Context, sender: str, msg: ChatMessage):
        question = ""
        for content in msg.content:
            if isinstance(content, TextContent):
                question = content.text
                break

        ctx.logger.info(f"💬 ASI:One query from {sender[:20]}…: {question[:80]}")

        await ctx.send(
            sender,
            ChatAcknowledgement(
                timestamp=datetime.now(timezone.utc),
                acknowledged_msg_id=msg.msg_id,
            ),
        )

        answer = _build_chat_response(question or "Summarize the current red zones.")

        await ctx.send(
            sender,
            ChatMessage(
                timestamp=datetime.now(timezone.utc),
                msg_id=uuid4(),
                content=[TextContent(type="text", text=answer), EndSessionContent(type="end-session")],
            ),
        )
        ctx.logger.info("✅ Chat reply sent.")

    @chat_proto.on_message(model=ChatAcknowledgement)
    async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
        ctx.logger.debug(f"ACK from {sender[:20]}… for {msg.acknowledged_msg_id}")

    narrator_agent.include(chat_proto, publish_manifest=True)


@narrator_agent.on_event("startup")
async def on_startup(ctx: Context):
    ctx.logger.info("━" * 55)
    ctx.logger.info("📣 Urban Nervous System — Narrator Agent")
    ctx.logger.info(f"📍 Address  : {narrator_agent.address}")
    ctx.logger.info(f"🔌 Port     : {AGENT_PORTS['narrator']}")
    ctx.logger.info(f"💬 ASI:One  : {'enabled' if _CHAT_PROTOCOL_AVAILABLE else 'unavailable (uagents_core missing)'}")
    ctx.logger.info("━" * 55)


if __name__ == "__main__":
    narrator_agent.run()
