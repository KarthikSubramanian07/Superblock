#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

ENV_FILE=".env"
EXAMPLE_FILE=".env.agentverse.example"
ADDRESS_FILE="agent_addresses.txt"

if [[ ! -f "$ENV_FILE" ]]; then
  if [[ -f "$EXAMPLE_FILE" ]]; then
    cp "$EXAMPLE_FILE" "$ENV_FILE"
    echo "[info] Created $ENV_FILE from $EXAMPLE_FILE"
  else
    echo "[error] Missing $EXAMPLE_FILE"
    exit 1
  fi
fi

echo "[info] Starting all 7 agents..."
./run_agents.sh

# Give agents a moment to boot and print startup addresses
sleep 3

extract_addr() {
  local log_file="$1"
  if [[ ! -f "$log_file" ]]; then
    echo ""
    return
  fi
  grep -Eo 'agent1[0-9a-z]+' "$log_file" | head -n 1 || true
}

INGESTION_ADDR="$(extract_addr logs/ingestion.log)"
MAPPING_ADDR="$(extract_addr logs/mapping.log)"
DIAGNOSIS_ADDR="$(extract_addr logs/diagnosis.log)"
SIMULATION_ADDR="$(extract_addr logs/simulation.log)"
PLANNER_ADDR="$(extract_addr logs/planner.log)"
NARRATOR_ADDR="$(extract_addr logs/narrator.log)"
COORDINATOR_ADDR="$(extract_addr logs/coordinator.log)"

cat > "$ADDRESS_FILE" <<EOF
SuperBlock Agent Addresses (for Agentverse registration)
=========================================================

Ingestion Agent:  ${INGESTION_ADDR}
Mapping Agent:    ${MAPPING_ADDR}
Diagnosis Agent:  ${DIAGNOSIS_ADDR}
Simulation Agent: ${SIMULATION_ADDR}
Planner Agent:    ${PLANNER_ADDR}
Narrator Agent:   ${NARRATOR_ADDR}
Coordinator Agent:${COORDINATOR_ADDR}

Quick checks:
- Agents running: $(ls logs/*.pid 2>/dev/null | wc -l | tr -d ' ')
- Logs folder: ${ROOT_DIR}/logs
EOF

echo ""
echo "[done] Agentverse prep complete."
echo "[done] Address file: ${ROOT_DIR}/${ADDRESS_FILE}"
echo ""
echo "Next manual steps:"
echo "1) Open ${ROOT_DIR}/${ADDRESS_FILE}"
echo "2) Run: python ${ROOT_DIR}/register_all_agents.py"
echo "3) Register each agent on Agentverse using these addresses"
echo "4) Capture the 7 Agentverse profile URLs + screenshot"
echo "5) Keep agents running during registration (stop later with ./run_agents.sh stop)"
