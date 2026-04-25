from __future__ import annotations

import argparse

import requests
from pydantic import Field
from uagents import Agent, Context, Model


class EdgePacketMessage(Model):
    user_id: str
    timestamp: str
    h3_index: str
    als_score: float = Field(ge=0.0, le=1.0)
    context: str
    noise_db: float = Field(ge=0.0, le=140.0)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a uAgent that forwards privacy-safe watch packets to FastAPI.",
    )
    parser.add_argument("--name", default="living-city-ingestor")
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument(
        "--seed",
        default="living-city-ingestor-seed",
        help="Development seed phrase for the demo agent.",
    )
    parser.add_argument(
        "--backend-url",
        default="http://127.0.0.1:8000/ingest/edge-packets",
        help="FastAPI edge ingestion endpoint.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    agent = Agent(name=args.name, seed=args.seed, port=args.port)

    @agent.on_message(model=EdgePacketMessage)
    async def handle_packet(ctx: Context, sender: str, msg: EdgePacketMessage) -> None:
        response = requests.post(
            args.backend_url,
            json={"packets": [msg.model_dump()]},
            timeout=30,
        )
        response.raise_for_status()
        ctx.logger.info("Forwarded packet from %s into backend tile store", sender)

    agent.run()


if __name__ == "__main__":
    main()
