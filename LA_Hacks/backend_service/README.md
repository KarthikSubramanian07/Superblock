# SuperBlock Backend Service

This folder contains the FastAPI backend, agent integration bridge, model artifacts wiring, and helper scripts.

For project overview, prize-track summary, and demo context, start from the repository root:

- `README.md`

---

## Quick Start

```bash
cd LA_Hacks/backend_service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Backend docs:

- `http://localhost:8000/docs`

---

## Key Endpoints

- `GET /health`
- `GET /map/tiles`
- `GET /agents`
- `POST /agents/orchestrate`
- `POST /simulate/intervention`
- `GET /planner/interventions`
- `GET /sponsors/dashboard`

---

## Agentverse Helpers

Agent scripts and registration helpers are in:

- `LA_Hacks/ingestion_agent.py`
- `LA_Hacks/mapping_agent.py`
- `LA_Hacks/diagnosis_agent.py`
- `LA_Hacks/simulation_agent.py`
- `LA_Hacks/planner_agent.py`
- `LA_Hacks/narrator_agent.py`
- `LA_Hacks/coordinator_agent.py`
- `LA_Hacks/run_agents.sh`
- `LA_Hacks/prepare_agentverse.sh`
- `LA_Hacks/register_all_agents.py`
