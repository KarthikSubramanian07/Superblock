# TESTING — Live Agents (Track 1)

Temporary doc for verifying the Track 1 multi-agent stack end-to-end on this branch (`greg/live-agents`). Delete or fold into the main README before submission.

---

## Prerequisites

### One-time host setup

| Tool | Version | Install |
|---|---|---|
| Python | 3.10+ (tested on 3.13) | python.org or pyenv |
| Node.js | 22 LTS | nodejs.org |
| Chrome or Brave | latest | for the Agentverse Inspector — Local Network Access prompt support |
| `git` | any | already installed |

### One-time accounts

- **Agentverse account** at https://agentverse.ai (sign in with same email as the ASI:One developer key).
- **ASI:One developer key** — already in `LA_Hacks/config.py` (`ASI_ONE_API_KEY`). No action unless you want to rotate.
- **Mapbox token** for the UI — only needed for step 5. Token goes in `superblock-ui/.env.local` as `VITE_MAPBOX_TOKEN=...`.

### Repo prep (run once per machine)

```bash
cd /path/to/Superblock
git checkout greg/live-agents
git pull origin greg/live-agents

# Python deps
cd LA_Hacks
python3 -m pip install --user -r requirements.txt
# expected: uagents, uagents-core, fastapi, uvicorn, python-dotenv, pydantic, requests, pandas, numpy

# UI deps
cd ../superblock-ui
npm install
```

### Verify install (~10 s)

```bash
cd /path/to/Superblock/LA_Hacks
python3 -c "import uagents, uagents_core, fastapi, uvicorn; print('deps OK')"
```

Expected: `deps OK`.

### Free up the demo ports before testing

Port 8000 (gateway) and 9000 (Bureau) must be free. Kill anything left over:

```bash
pkill -f 'node.*server.js'      # mockagent
pkill -f 'orchestrator.py'      # previous Bureau
pkill -f 'uvicorn gateway:app'  # previous gateway
lsof -nP -iTCP:8000 -sTCP:LISTEN   # should print nothing
lsof -nP -iTCP:9000 -sTCP:LISTEN   # should print nothing
```

---

## Test plan

You'll need 4 terminals open. All start at repo root.

### Terminal 1 — Bureau (the 6 agents)

```bash
cd LA_Hacks
python3 orchestrator.py
```

**Working signal (last ~15 lines):**

```
========================================================================
AGENT ADDRESSES — paste into config.py::AGENT_ADDRESSES
========================================================================
    "ingestion":  "agent1qfrjfv625jhfz5n6ur37vr8h0xx9mdhgnu6sfhwr2yksy2hfxgtjqtku9tr",
    ... (5 more)
========================================================================
INFO: [bureau]: Starting server on http://0.0.0.0:9000
INFO: [narrator_agent]: Manifest published successfully: AgentChatProtocol
INFO: [<agent>]: Manifest published successfully: <protocol>   x8 total
INFO: [<agent>]: Agent registration status updated to active   x6
INFO: [bureau]: Batch registration on Almanac API successful
```

**Expected (non-fatal) warnings:**

- `I do not have enough funds to register on Almanac contract` — testnet on-chain registration; mailbox-based discovery works without it.
- `Agent mailbox not found: create one using the agent inspector` — clears after step 3.

**Pass criterion:** all 6 agents say `registration status updated to active` AND there is exactly one `Manifest published successfully: AgentChatProtocol` line under `narrator_agent`.

Leave terminal 1 running.

---

### Terminal 2 — gateway (FastAPI on :8000 mirroring mockagent contract)

```bash
cd LA_Hacks
uvicorn gateway:app --host 127.0.0.1 --port 8000
```

If `uvicorn` isn't on PATH:

```bash
~/Library/Python/3.13/bin/uvicorn gateway:app --host 127.0.0.1 --port 8000
```

**Working signal:**

```
INFO: Started server process [...]
INFO: Application startup complete.
INFO: Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

Leave terminal 2 running.

---

### Terminal 3 — gateway smoke tests

```bash
curl -s http://127.0.0.1:8000/health
# expected: "OK"

curl -s 'http://127.0.0.1:8000/diagnosis?h3_index=8b29a1d71911fff' | python3 -m json.tool
# expected: failure_mode = "Composite Failure", recommendations populated
# (if this matches, you're hitting real diagnosis_agent rules, not mockagent)

curl -s -X POST http://127.0.0.1:8000/simulate \
  -H 'Content-Type: application/json' \
  -d '{"h3_index":"8b29a1d71911fff","intervention_id":"shade_canopy","als_before":0.84}'
# expected: {"als_before":0.84,"als_after":0.6,"als_delta":-0.24,"percent_reduction":29}
```

If all three match, the gateway is wired through to the agents.

---

### Step 3 — Create one Agentverse mailbox per agent (browser)

**Prereq:** terminal 1 (Bureau) must still be running.

**Browser:** Chrome or Brave.

**First-time only:** when you visit any inspect URL, the browser shows a **"Local Network Access"** permission prompt for `agentverse.ai`. Click **Allow**. Without this the Inspector cannot see the agent on `127.0.0.1:9000`.

For each row below: open the URL → click **Connect** (top right) → select **Mailbox** → click **Finish**. Page should end with a green **Connected** badge.

| # | Agent | Inspector URL |
|---|---|---|
| 1 | **narrator** (do first) | https://agentverse.ai/inspect/?uri=http%3A//127.0.0.1%3A9000&address=agent1qg8ej0nznmzqgdj62k5tghezyes0wlrd35sf9p6uy02nunz325s5sme2cl0 |
| 2 | ingestion | https://agentverse.ai/inspect/?uri=http%3A//127.0.0.1%3A9000&address=agent1qfrjfv625jhfz5n6ur37vr8h0xx9mdhgnu6sfhwr2yksy2hfxgtjqtku9tr |
| 3 | mapping | https://agentverse.ai/inspect/?uri=http%3A//127.0.0.1%3A9000&address=agent1qgnhw5kpwtz3xjd3y8qsj7mcufdpes4mgz2n5l700780vvp8law052j459v |
| 4 | diagnosis | https://agentverse.ai/inspect/?uri=http%3A//127.0.0.1%3A9000&address=agent1q0muzg3k6nkczl849kaw7q62kn095khrpu4hg3nh55vw4vu8knuvkszhl82 |
| 5 | simulation | https://agentverse.ai/inspect/?uri=http%3A//127.0.0.1%3A9000&address=agent1qd5kx6uulfkdsfee2x20sf397hvlts8xz6fq534zsg3pkyf9vl3z2xqeq6u |
| 6 | planner | https://agentverse.ai/inspect/?uri=http%3A//127.0.0.1%3A9000&address=agent1q0nuqrnterfxycglj2q0tu2s49nr8rad8knff23r0u9ney2ncggmsk07f7v |

**Confirm:**

- The `Agent mailbox not found` warning in terminal 1 stops appearing on the next manifest refresh.
- Each profile at `https://agentverse.ai/agents/details/<address>/profile` shows status **active** with a Mailbox badge.

These mailboxes are tied to the agent's seed — they survive restarts. One-time setup.

---

### Step 4 — ASI:One chat → Narrator (the prize-criterion demo)

1. Open https://asi1.ai (sign in).
2. Start a new chat session.
3. Address the narrator agent (typically by pasting/selecting):
   `agent1qg8ej0nznmzqgdj62k5tghezyes0wlrd35sf9p6uy02nunz325s5sme2cl0`
4. Ask: **"What is the best $10k fix for the red zone in DTLA?"**

**Working signal in terminal 1:**

```
INFO: [narrator_agent]: ASI:One query from agent1q...: What is the best $10k fix...
INFO: [narrator_agent]: Chat reply sent.
```

**Working signal in ASI:One UI:** 2–4 paragraph reply that names a specific intervention, cites Biological Relief Coefficient, gives a predicted ALS reduction %, ends with a next step.

**Save the resulting shared-chat URL** — it's a required submission deliverable.

---

### Terminal 4 — UI LIVE mode

```bash
cd superblock-ui
npm run dev
```

Open the Vite URL (typically http://localhost:5173).

1. Flip the **demo/LIVE toggle** in the UI to LIVE.
2. Click hotspot **Civic Center area** (h3 `8b29a1d71911fff`, ALS 0.84).
3. Diagnosis panel must show **Composite Failure** + the root causes/recommendations from `diagnosis_agent.py` rules (not mockagent's static `Heat exposure`).
4. Run a simulate intervention. `als_after`, `percent_reduction` come from gateway, not mockagent's static math.

If the toggle stays on mock: the UI's health probe is being routed elsewhere — confirm `mockagent/server.js` is **not** also running on :8000 (only the gateway should be).

---

## Definition of Done — what "fully working" looks like

- [ ] Terminal 1: 6 agents `active`, 8 manifests published incl. `AgentChatProtocol` on narrator.
- [ ] Terminal 2: gateway up, three smoke curls return expected shapes.
- [ ] Browser: 6 mailboxes connected via Inspector. 6 Agentverse profile pages load with `active` + Mailbox badge.
- [ ] ASI:One: narrator answers a $10k DTLA question with a ranked intervention. Shared-chat URL saved.
- [ ] UI on :5173: LIVE toggle on, hotspot click → real diagnosis from agents, real simulate numbers.

---

## Troubleshooting cheatsheet

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: uagents_core` | uagents-core not installed | `pip install -r LA_Hacks/requirements.txt` |
| `Address already in use :8000` | mockagent still running | `pkill -f 'node.*server.js'`; restart gateway |
| `Address already in use :9000` | previous Bureau didn't shut | `pkill -f orchestrator.py`; restart Bureau |
| Inspector page is empty / "Cannot connect" | Bureau not running, or Local Network Access blocked | restart Bureau; allow LNA in browser site settings |
| ASI:One chat hangs / no reply | Narrator mailbox not created | redo step 3 row 1 |
| `[narrator_agent]: ASI:One unavailable` in chat reply | API key invalid or no internet | check `ASI_ONE_API_KEY` in `LA_Hacks/config.py` or env |
| Gateway `/diagnosis` returns mockagent fallback (no `failure_mode` field) | h3_index not in `mockData.json::hotspots` | use `8b29a1d71911fff`, `8b29a1d757a4fff`, or `8b29a1d75b9bfff` |
| UI LIVE toggle keeps falling back to demo | UI health probe failing | confirm only gateway listens on :8000; check browser console for CORS errors |
