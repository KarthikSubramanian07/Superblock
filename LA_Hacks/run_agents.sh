#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

if [[ ! -f ".env" ]]; then
  echo "[info] .env not found in LA_Hacks/."
  echo "[info] Create one from template: cp .env.agentverse.example .env"
fi

mkdir -p logs

start_agent() {
  local name="$1"
  local file="$2"
  local log_file="logs/${name}.log"
  echo "[start] ${name} -> ${file}"
  nohup python "$file" > "$log_file" 2>&1 &
  echo $! > "logs/${name}.pid"
  sleep 0.4
}

stop_if_running() {
  local name="$1"
  local pid_file="logs/${name}.pid"
  if [[ -f "$pid_file" ]]; then
    local pid
    pid="$(cat "$pid_file")"
    if kill -0 "$pid" >/dev/null 2>&1; then
      echo "[stop] ${name} (${pid})"
      kill "$pid" || true
      sleep 0.2
    fi
    rm -f "$pid_file"
  fi
}

if [[ "${1:-start}" == "stop" ]]; then
  for n in ingestion mapping diagnosis simulation planner narrator coordinator; do
    stop_if_running "$n"
  done
  echo "[done] stopped all agents"
  exit 0
fi

for n in ingestion mapping diagnosis simulation planner narrator coordinator; do
  stop_if_running "$n"
done

start_agent "ingestion" "ingestion_agent.py"
start_agent "mapping" "mapping_agent.py"
start_agent "diagnosis" "diagnosis_agent.py"
start_agent "simulation" "simulation_agent.py"
start_agent "planner" "planner_agent.py"
start_agent "narrator" "narrator_agent.py"
start_agent "coordinator" "coordinator_agent.py"

echo "[done] all agents started"
echo "[logs] tail -f LA_Hacks/logs/*.log"
echo "[stop] ./LA_Hacks/run_agents.sh stop"
