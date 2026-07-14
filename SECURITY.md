# Security: credentials and production mode for SuperBlock

## Why this exists

Old commits (for example `0795c5b`, `bb6d34c`, `d89f150`) once contained live credentials in the tree.
Removing them from `main` does **not** erase them from git history. Anyone who cloned the repo
could still recover them. Treat those values as public.

This checklist is what "rotate secrets + DEMO_MODE=false + Auth0" means in practice.

---

## 1. Rotate secrets (must be done in provider dashboards)

I cannot revoke or reissue third-party credentials from this repo. Do these once:

### ASI:One (Fetch.ai)
1. Open https://asi1.ai (Account → API Keys)
2. **Revoke / delete** any key that ever lived in this repo (including keys that were later
   deleted from `main` but may still exist in history)
3. Create a **new** key
4. Put it only in local/deploy secrets:
   - `LA_Hacks/backend_service/.env.local` → `ASI_ONE_API_KEY=...`
   - Or your hosting secret store (never commit)

### MongoDB Atlas
1. Open https://cloud.mongodb.com → Database Access
2. For the user that appeared in the old URI (historically `superblock@...`):
   - Edit user → **Edit Password** (or delete + recreate)
3. Update Network Access if it was overly open
4. Put the new URI in `.env.local` as `MONGO_URI=mongodb+srv://...`
5. Optionally review Atlas Activity / logs for unexpected access after the leak window

### Fetch.ai / Agentverse agent seeds
Agent private keys are derived from seed phrases. Public seeds in history mean those agents
can be impersonated.

1. Generate **new** seeds (long random phrases) for each agent
2. Set env vars before launching agents:
   - `INGESTION_AGENT_SEED`, `MAPPING_AGENT_SEED`, `DIAGNOSIS_AGENT_SEED`,
     `SIMULATION_AGENT_SEED`, `PLANNER_AGENT_SEED`, `NARRATOR_AGENT_SEED`
   - or a single `AGENT_SEED` for the ASI skill script
3. Restart agents so they register **new** Agentverse addresses
4. Update README / Almanac links to the new address(es)
5. Retire old Agentverse listings if still visible

### ZETIC
If `ztc_live_...` was ever a real key, rotate it in the Melange dashboard and set
`ZETIC_DEPLOYMENT_KEY` in env only.

### Auth0 (needed when DEMO_MODE=false)
1. Create/open an Auth0 tenant → Applications → API (or SPA + API)
2. Note:
   - Domain (e.g. `your-tenant.us.auth0.com`) → `AUTH0_DOMAIN`
   - API Identifier / Audience → `AUTH0_AUDIENCE`
3. Configure the SPA to obtain access tokens for that audience
4. Put both values in `.env.local` / deploy secrets

GitHub **secret scanning** and **push protection** are enabled on this repo to catch future accidents.

---

## 2. Production mode (what the code does now)

| Setting | Local hackathon / CI | Public deploy |
|---------|----------------------|---------------|
| `DEMO_MODE` | `true` (explicit) | `false` (default if unset) |
| Write routes (`/ingest/*`, `/demo/reset`, `/agents/orchestrate*`) | Open | Require Auth0 bearer |
| World ID `is_mock` | Allowed | Rejected |
| Client `is_verified_human` | Ignored; server decides | Ignored; real proof required |
| Agent seed fallbacks | Allowed | Env required |

Example production `.env.local`:

```bash
DEMO_MODE=false
AUTH0_DOMAIN=your-tenant.us.auth0.com
AUTH0_AUDIENCE=https://api.superblock.example
ALLOWED_ORIGINS=https://your-ui.example
ASI_ONE_API_KEY=...
MONGO_URI=mongodb+srv://...
INGESTION_AGENT_SEED=...
# ...other agent seeds...
```

Example local demo:

```bash
DEMO_MODE=true
```

CI already sets `DEMO_MODE=true`.

---

## 3. Optional: purge secrets from git history

Rotating credentials is enough for safety. Rewriting history (BFG / `git filter-repo`) is
optional and disruptive for every clone. Only do it if you also force-push and coordinate
with anyone who forked the repo.

---

## 4. Verify

```bash
# Should reject unauthenticated writes when production-configured:
DEMO_MODE=false AUTH0_DOMAIN=example.auth0.com AUTH0_AUDIENCE=https://api.example \
  uvicorn app.main:app
# POST /ingest/edge-packets without Bearer → 401

# Local demo still works when opted in:
DEMO_MODE=true uvicorn app.main:app
```
