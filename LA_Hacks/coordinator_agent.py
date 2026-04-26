import os
import requests
from pydantic import BaseModel, Field
from uagents import Agent, Context, Protocol

from config import AGENT_SEEDS, AGENT_PORTS, endpoint_for

BACKEND_ORCHESTRATE_URL = os.getenv(
    "BACKEND_ORCHESTRATE_URL",
    "http://127.0.0.1:8000/agents/orchestrate",
)


class CoordinatorQuery(BaseModel):
    question: str = Field(description="User query for city climate analysis")
    h3_index: str | None = Field(default=None, description="Optional target tile")


class CoordinatorReply(BaseModel):
    answer: str
    selected_h3_index: str | None = None
    agent_call_order: list[str] = []


coordinator_agent = Agent(
    name="coordinator_agent",
    seed=AGENT_SEEDS["coordinator"],
    port=AGENT_PORTS["coordinator"],
    endpoint=[endpoint_for("coordinator")],
)

coordinator_proto = Protocol("coordinator")


@coordinator_proto.on_message(model=CoordinatorQuery, replies=CoordinatorReply)
async def handle_query(ctx: Context, sender: str, msg: CoordinatorQuery):
    try:
        payload: dict[str, str] = {}
        if msg.h3_index:
            payload["h3_index"] = msg.h3_index

        response = requests.post(
            BACKEND_ORCHESTRATE_URL,
            json=payload,
            timeout=25,
        )
        response.raise_for_status()
        data = response.json()

        selected_h3 = data.get("selected_h3_index")
        diagnosis = data.get("diagnosis_alert", {})
        stressor = diagnosis.get("primary_stressor", "Unknown")

        summary = (
            f"Top hotspot: {selected_h3}. Primary stressor: {stressor}. "
            "Workflow executed across ingestion, mapping, diagnosis, simulation, planner, and narrator."
        )

        await ctx.send(
            sender,
            CoordinatorReply(
                answer=summary,
                selected_h3_index=selected_h3,
                agent_call_order=[
                    "ingestion_agent",
                    "mapping_agent",
                    "diagnosis_agent",
                    "simulation_agent",
                    "planner_agent",
                    "narrator_agent",
                ],
            ),
        )
    except Exception as exc:
        await ctx.send(
            sender,
            CoordinatorReply(answer=f"Coordinator error: {exc}"),
        )


@coordinator_agent.on_event("startup")
async def on_startup(ctx: Context):
    ctx.logger.info("━" * 55)
    ctx.logger.info("🧭 SuperBlock Coordinator Agent")
    ctx.logger.info(f"📍 Address : {coordinator_agent.address}")
    ctx.logger.info(f"🔌 Port    : {AGENT_PORTS['coordinator']}")
    ctx.logger.info(f"🔗 Backend : {BACKEND_ORCHESTRATE_URL}")
    ctx.logger.info("━" * 55)


if __name__ == "__main__":
    coordinator_agent.include(coordinator_proto, publish_manifest=True)
    coordinator_agent.run()
