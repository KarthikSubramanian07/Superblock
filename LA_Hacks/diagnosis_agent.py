"""
diagnosis_agent.py
─────────────────────────────────────────────────────────────────────────────
Urban Nervous System — Agent 3: Diagnosis
─────────────────────────────────────────────────────────────────────────────
Responsibilities:
  1. Receive Red Zone alerts from the Mapping Agent
  2. Classify urban failure mode from ALS signal pattern
  3. Query ASI:One (via REST) for deeper reasoning when confidence < 80%
  4. Forward DiagnosisResult to Simulation Agent
  5. Respond to live chat queries (plain Protocol — no uagents_core dep)
"""
import os
import json
import requests
from uagents import Agent, Context, Protocol
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────
AGENT_SEEDS = {
    "ingestion":  "ingestion-agent-seed-la-hacks-2026",
    "mapping":    "mapping-agent-seed-la-hacks-2026",
    "diagnosis":  "diagnosis-agent-seed-la-hacks-2026",
    "simulation": "simulation-agent-seed-la-hacks-2026",
    "planner":    "planner-agent-seed-la-hacks-2026",
    "narrator":   "narrator-agent-seed-la-hacks-2026",
}
AGENT_PORTS = {
    "ingestion":  8000,
    "mapping":    8001,
    "diagnosis":  8002,
    "simulation": 8003,
    "planner":    8004,
    "narrator":   8005,
}

# Paste Simulation Agent address after running simulation_agent.py
SIMULATION_AGENT_ADDRESS = "agent1q_PASTE_SIMULATION_ADDRESS_HERE"

# ASI:One / Fetch.ai API — set in .env
ASI_ONE_API_KEY  = os.getenv("ASI_ONE_API_KEY", "")
ASI_ONE_ENDPOINT = os.getenv("ASI_ONE_ENDPOINT", "https://api.asi1.ai/v1/chat/completions")
ASI_ONE_MODEL    = os.getenv("ASI_ONE_MODEL", "asi1-mini")

# ─────────────────────────────────────────────────────────────────────────────
# Data Models
# ─────────────────────────────────────────────────────────────────────────────
class RedZoneAlert(BaseModel):
    """Received from Mapping Agent."""
    h3_index:             str
    avg_als:              float
    sample_count:         int
    context_distribution: dict   # {"Stationary": 0.8, "Walking": 0.15, "Transit": 0.05}
    noise_bucket:         str    # "Low" | "Medium" | "High"
    heat_flag:            bool
    gait_quality:         str    # "Good" | "Degraded"
    duration_minutes:     float

class DiagnosisResult(BaseModel):
    """Forwarded to Simulation Agent."""
    h3_index:        str
    failure_mode:    Literal[
        "Acoustic Failure",
        "Heat Exhaustion Onset",
        "Air Quality / Crowding Stress",
        "Infrastructure Friction",
        "Composite Failure",
        "Normal",
    ]
    severity:        Literal["low", "moderate", "high", "critical"]
    confidence:      float
    signal_evidence: List[str]
    root_causes:     List[str]
    recommendations: List[str]
    avg_als:         float
    asi_reasoning:   Optional[str] = None

class ChatQuery(BaseModel):
    """Plain chat query — no uagents_core dependency."""
    question: str = Field(description="Natural language query from stakeholder")

class ChatReply(BaseModel):
    """Plain chat reply."""
    answer: str

# ─────────────────────────────────────────────────────────────────────────────
# Rule-Based Classifier
# ─────────────────────────────────────────────────────────────────────────────
def classify_failure_mode(alert: RedZoneAlert) -> tuple[str, float, list[str]]:
    """
    Pattern-match on tile signal profile → (failure_mode, confidence, evidence).
    Priority order matters — Acoustic is checked before Composite so a
    high-noise stationary tile doesn't fall through to the catch-all.
    """
    als  = alert.avg_als
    stat = alert.context_distribution.get("Stationary", 0.0)
    walk = alert.context_distribution.get("Walking", 0.0)
    tran = alert.context_distribution.get("Transit", 0.0)

    evidence = [
        f"Avg ALS {als:.2f}",
        f"Stationary {stat:.0%} / Walking {walk:.0%} / Transit {tran:.0%}",
        f"Noise: {alert.noise_bucket}",
        f"Heat flag: {'Yes' if alert.heat_flag else 'No'}",
        f"Gait: {alert.gait_quality}",
        f"Duration: {alert.duration_minutes:.1f} min",
        f"Sample count: {alert.sample_count}",
    ]

    # ── Acoustic Failure ───────────────────────────────────────────────────
    if als >= 0.70 and stat >= 0.65 and alert.noise_bucket == "High":
        return "Acoustic Failure", 0.88, evidence

    # ── Heat Exhaustion Onset ──────────────────────────────────────────────
    if als >= 0.65 and walk >= 0.55 and alert.heat_flag and alert.gait_quality == "Degraded":
        return "Heat Exhaustion Onset", 0.85, evidence

    # ── Air Quality / Crowding Stress ──────────────────────────────────────
    if (als >= 0.68 and tran >= 0.50
            and alert.heat_flag
            and alert.noise_bucket in ("Medium", "High")):
        return "Air Quality / Crowding Stress", 0.80, evidence

    # ── Infrastructure Friction ────────────────────────────────────────────
    if (0.50 <= als <= 0.72
            and walk >= 0.60
            and alert.gait_quality == "Degraded"
            and not alert.heat_flag):
        return "Infrastructure Friction", 0.75, evidence

    # ── Composite Failure ──────────────────────────────────────────────────
    if als >= 0.70:
        return "Composite Failure", 0.55, evidence

    # ── Normal ────────────────────────────────────────────────────────────
    return "Normal", 0.90, evidence


def severity_from_als(als: float) -> str:
    if als >= 0.85: return "critical"
    if als >= 0.70: return "high"
    if als >= 0.55: return "moderate"
    return "low"


FAILURE_DETAILS = {
    "Acoustic Failure": {
        "root_causes": [
            "Sustained ambient noise above 80 dB (construction, traffic, transit)",
            "Lack of acoustic buffering infrastructure",
            "High stationary dwell time amplifying cumulative noise exposure",
        ],
        "recommendations": [
            "Install noise barriers or sound-absorbing canopy",
            "Reroute heavy vehicle traffic during peak pedestrian hours",
            "Add a designated quiet zone with seating",
        ],
    },
    "Heat Exhaustion Onset": {
        "root_causes": [
            "Insufficient shade coverage on active pedestrian routes",
            "High surface albedo from pavement and dark roofing",
            "Gait degradation signals thermal stress onset before HR peak",
        ],
        "recommendations": [
            "Deploy shade canopy along primary walking corridors",
            "Install misting stations at key pedestrian nodes",
            "Add cool-surface pavement or reflective coating",
        ],
    },
    "Air Quality / Crowding Stress": {
        "root_causes": [
            "Pedestrian crowding suppressing SpO₂ and elevating respiratory rate",
            "Poor air circulation in transit-heavy corridors",
            "Combined heat and crowd density increasing perceived exertion",
        ],
        "recommendations": [
            "Extend walk signal timing to reduce pedestrian bunching",
            "Add pedestrian bridge or grade separation at bottleneck",
            "Increase ventilation or plant air-filtering trees along corridor",
        ],
    },
    "Infrastructure Friction": {
        "root_causes": [
            "Uneven pavement or missing curb cuts degrading gait quality",
            "Grade barriers slowing stair ascent and descent",
            "Poor wayfinding forcing inefficient pedestrian routing",
        ],
        "recommendations": [
            "Resurface sidewalk and install compliant curb cuts",
            "Add parklet / green rest space for recovery",
            "Improve wayfinding signage at key decision nodes",
        ],
    },
    "Composite Failure": {
        "root_causes": [
            "Multiple simultaneous stressors — no single dominant signal",
            "Elevated ALS without a clean pattern suggests compound cause",
        ],
        "recommendations": [
            "Deploy combined shade + noise barrier intervention bundle",
            "Increase sensor coverage in this tile for better signal resolution",
            "Prioritize rapid walkthrough survey before intervention selection",
        ],
    },
    "Normal": {
        "root_causes": [],
        "recommendations": ["No intervention needed — continue monitoring."],
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# ASI:One Query
# ─────────────────────────────────────────────────────────────────────────────
def query_asi_one(alert: RedZoneAlert, rule_diagnosis: str) -> Optional[str]:
    """
    Sends the tile's signal profile to ASI:One for a deeper reasoning pass.
    Falls back gracefully if API key is not set or the call fails.
    """
    if not ASI_ONE_API_KEY:
        return None

    prompt = f"""
You are an urban biometric stress analyst for the Urban Nervous System project.
A city block in Downtown LA has been flagged as a Red Zone.

Here is its live signal profile from Apple Watch edge sensors:
  H3 Tile:            {alert.h3_index}
  Avg ALS Score:      {alert.avg_als:.3f}  (0.0 = calm, 1.0 = maximum stress)
  Duration:           {alert.duration_minutes:.1f} minutes in Red Zone
  Sample count:       {alert.sample_count} devices
  Movement context:   {alert.context_distribution}
  Noise level:        {alert.noise_bucket}
  Heat flag:          {'Yes — wrist temperature elevated > 1.5°C above baseline' if alert.heat_flag else 'No'}
  Gait quality:       {alert.gait_quality}

The rule-based classifier suggests: "{rule_diagnosis}"

Please:
1. Confirm or challenge the rule-based diagnosis in 2 sentences.
2. Identify any secondary stressors the rules may have missed.
3. Suggest the single most impactful intervention for this specific signal profile.

Be concise — this response will be displayed in a live stakeholder dashboard.
"""
    try:
        response = requests.post(
            ASI_ONE_ENDPOINT,
            headers={
                "Authorization": f"Bearer {ASI_ONE_API_KEY}",
                "Content-Type":  "application/json",
            },
            json={
                "model": ASI_ONE_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are an expert in urban design and human physiological "
                            "stress. You interpret community biometric signals to identify "
                            "urban infrastructure failures and recommend interventions."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 300,
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[ASI:One unavailable: {e}]"

# ─────────────────────────────────────────────────────────────────────────────
# Agent & Protocols
# ─────────────────────────────────────────────────────────────────────────────
diagnosis_agent = Agent(
    name="diagnosis_agent",
    seed=AGENT_SEEDS["diagnosis"],
    port=AGENT_PORTS["diagnosis"],
    endpoint=[f"http://127.0.0.1:{AGENT_PORTS['diagnosis']}/submit"],
)

diagnosis_proto = Protocol("diagnosis")
chat_proto      = Protocol("chat")          # ← plain Protocol, same as ingestion pattern

# Cache the latest result for chat queries
_latest_result: Optional[DiagnosisResult] = None

# ─────────────────────────────────────────────────────────────────────────────
# Message Handlers
# ─────────────────────────────────────────────────────────────────────────────
@diagnosis_proto.on_message(model=RedZoneAlert, replies=DiagnosisResult)
async def handle_diagnosis(ctx: Context, sender: str, msg: RedZoneAlert):
    global _latest_result

    ctx.logger.info(
        f"🔍 Analyzing Red Zone | Tile {msg.h3_index[:12]}... | "
        f"ALS={msg.avg_als:.3f} | n={msg.sample_count}"
    )

    # Step 1 — Fast rule-based classification
    failure_mode, confidence, evidence = classify_failure_mode(msg)
    details  = FAILURE_DETAILS[failure_mode]
    severity = severity_from_als(msg.avg_als)

    ctx.logger.info(
        f"  Rule classifier → [{failure_mode}] | "
        f"Severity: {severity} | Confidence: {confidence:.0%}"
    )

    # Step 2 — Call ASI:One for deeper reasoning when confidence is borderline
    asi_reasoning = None
    if confidence < 0.80:
        ctx.logger.info("  Confidence < 80% — querying ASI:One for deeper analysis...")
        asi_reasoning = query_asi_one(msg, failure_mode)
        if asi_reasoning:
            ctx.logger.info(f"  ASI:One: {asi_reasoning[:80]}...")

    # Step 3 — Build result
    result = DiagnosisResult(
        h3_index=        msg.h3_index,
        failure_mode=    failure_mode,
        severity=        severity,
        confidence=      confidence,
        signal_evidence= evidence,
        root_causes=     details["root_causes"],
        recommendations= details["recommendations"],
        avg_als=         msg.avg_als,
        asi_reasoning=   asi_reasoning,
    )
    _latest_result = result

    ctx.logger.info(
        f"✅ Diagnosis complete → [{failure_mode}] | "
        f"Confidence: {confidence:.0%} | Severity: {severity}"
    )

    # Step 4 — Forward to Simulation Agent
    if SIMULATION_AGENT_ADDRESS != "agent1q_PASTE_SIMULATION_ADDRESS_HERE":
        await ctx.send(SIMULATION_AGENT_ADDRESS, result)
        ctx.logger.info("📤 Forwarded to Simulation Agent")
    else:
        ctx.logger.warning(
            "⚠️  SIMULATION_AGENT_ADDRESS not set — diagnosis complete but not forwarded."
        )


@chat_proto.on_message(model=ChatQuery, replies=ChatReply)
async def handle_chat(ctx: Context, sender: str, msg: ChatQuery):
    """Respond to live natural language queries from stakeholders."""
    query = msg.question.lower()
    ctx.logger.info(f"💬 Chat query: '{query[:60]}'")

    if _latest_result is None:
        reply = (
            "No Red Zones currently diagnosed. "
            "The Urban Nervous System is monitoring Downtown LA — all clear."
        )
    elif any(w in query for w in ["fail", "wrong", "problem", "what"]):
        reply = (
            f"Current diagnosis for tile {_latest_result.h3_index[:12]}...: "
            f"{_latest_result.failure_mode} (severity: {_latest_result.severity}, "
            f"confidence: {_latest_result.confidence:.0%}). "
            f"Evidence: {'; '.join(_latest_result.signal_evidence[:3])}."
        )
    elif any(w in query for w in ["cause", "why"]):
        causes = "; ".join(_latest_result.root_causes) or "No root causes identified."
        reply = f"Root causes for [{_latest_result.failure_mode}]: {causes}"
    elif any(w in query for w in ["fix", "recommend", "best", "intervention"]):
        recs  = "; ".join(_latest_result.recommendations)
        reply = (
            f"Recommended interventions for [{_latest_result.failure_mode}] "
            f"at {_latest_result.h3_index[:12]}...: {recs}"
        )
    elif "confidence" in query:
        reply = (
            f"Diagnosis confidence: {_latest_result.confidence:.0%}. "
            + (
                f"ASI:One note: {_latest_result.asi_reasoning}"
                if _latest_result.asi_reasoning
                else "Rule-based classifier used — high signal clarity."
            )
        )
    else:
        reply = (
            f"Diagnosis Agent active. Latest: [{_latest_result.failure_mode}] "
            f"at tile {_latest_result.h3_index[:12]}... | "
            f"ALS={_latest_result.avg_als:.2f} | Severity={_latest_result.severity}. "
            "Ask me: 'What is failing?', 'Why?', 'What is the best fix?'"
        )

    await ctx.send(sender, ChatReply(answer=reply))

# ─────────────────────────────────────────────────────────────────────────────
# Startup
# ─────────────────────────────────────────────────────────────────────────────
@diagnosis_agent.on_event("startup")
async def on_startup(ctx: Context):
    ctx.logger.info("━" * 55)
    ctx.logger.info("🔬 Urban Nervous System — Diagnosis Agent")
    ctx.logger.info(f"📍 Address    : {diagnosis_agent.address}")
    ctx.logger.info(f"🔌 Port       : {AGENT_PORTS['diagnosis']}")
    ctx.logger.info(f"🤖 Simulation : {SIMULATION_AGENT_ADDRESS[:30]}")