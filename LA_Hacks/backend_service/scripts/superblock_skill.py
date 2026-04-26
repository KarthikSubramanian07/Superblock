"""
superblock_skill.py — OmegaClaw skill module for Superblock City Planner
Calls the local Superblock FastAPI backend to get urban stress analysis.
"""
import requests
import json


def superblock_analyze(query: str = "analyze hotspots", timeout: int = 30) -> str:
    """Query the Superblock Urban Nervous System for city stress analysis."""
    try:
        # Call the backend orchestration endpoint
        response = requests.post(
            "http://host.docker.internal:8000/agents/orchestrate",
            json={},
            timeout=int(timeout),
        )
        if response.status_code != 200:
            return f"error: backend returned {response.status_code}"

        data = response.json()

        # Build a readable summary
        h3 = data.get("selected_h3_index", "unknown")
        diag = data.get("diagnosis_result", data.get("diagnosis_alert", {}))
        failure = diag.get("failure_mode", "Unknown")
        severity = diag.get("severity", "unknown")
        als = diag.get("avg_als", 0)

        sim = data.get("simulation_scenarios", data.get("simulation_request", {}))
        plan = data.get("ranked_plan", {})
        narrative = data.get("narrative_report", {})

        # Get recommendations
        recs = diag.get("recommendations", [])
        rec_text = "; ".join(recs[:3]) if recs else "No recommendations yet"

        # Get top intervention
        ranked = plan.get("ranked_interventions", [])
        top_intervention = ranked[0].get("scenario_name", "None") if ranked else "None"
        budget = plan.get("total_budget", "N/A")

        exec_summary = narrative.get("executive_summary", "")

        result = (
            f"🏙️ SUPERBLOCK URBAN STRESS ANALYSIS\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📍 Tile: {h3}\n"
            f"🔴 Failure Mode: {failure}\n"
            f"⚠️  Severity: {severity}\n"
            f"📊 Avg Stress (ALS): {als:.3f}\n"
            f"💡 Top Intervention: {top_intervention}\n"
            f"💰 Total Budget: ${budget}\n"
            f"📋 Recommendations: {rec_text}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{exec_summary}"
        )
        return result

    except requests.exceptions.ConnectionError:
        return "error: Cannot connect to Superblock backend at port 8000. Is it running?"
    except Exception as e:
        return f"error: {e}"


def superblock_simulate(intervention: str = "shade_canopy", budget: int = 25000, timeout: int = 30) -> str:
    """Simulate a specific intervention on the highest-stress tile."""
    try:
        # First get the hotspot
        orch = requests.post(
            "http://host.docker.internal:8000/agents/orchestrate",
            json={},
            timeout=int(timeout),
        )
        if orch.status_code != 200:
            return f"error: backend returned {orch.status_code}"

        h3 = orch.json().get("selected_h3_index", "")

        # Run simulation
        sim = requests.post(
            "http://host.docker.internal:8000/simulate/intervention",
            json={
                "h3_index": h3,
                "intervention_type": str(intervention),
                "intensity": 0.8,
                "budget_usd": float(budget),
            },
            timeout=int(timeout),
        )
        if sim.status_code != 200:
            return f"error: simulation returned {sim.status_code}"

        data = sim.json()
        before = data.get("before", {})
        after = data.get("after", {})

        result = (
            f"🔬 INTERVENTION SIMULATION: {data.get('intervention_type', intervention)}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📍 Tile: {h3}\n"
            f"💰 Cost: ${data.get('estimated_cost_usd', 'N/A')}\n"
            f"📉 ALS Reduction: {data.get('estimated_als_reduction', 0):.3f}\n"
            f"🔇 Noise Reduction: {data.get('estimated_noise_reduction_db', 0):.1f} dB\n"
            f"⭐ Impact Score: {data.get('impact_score', 0):.2f}\n"
            f"\n"
            f"Before → After:\n"
            f"  Stress: {before.get('avg_als', 0):.3f} → {after.get('avg_als', 0):.3f}\n"
            f"  Noise:  {before.get('noise_db', 0):.1f} → {after.get('noise_db', 0):.1f} dB\n"
            f"  Status: {before.get('status', '?')} → {after.get('status', '?')}\n"
        )
        return result

    except Exception as e:
        return f"error: {e}"
