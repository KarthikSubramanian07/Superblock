# Superblock — Team Integration Guide

## What the frontend already does

The UI is fully built and running with synthetic demo data. It is already wired to connect to your backend automatically — you don't need to change anything on the frontend side. The moment your server is up at `localhost:8000`, the frontend detects it and switches from demo data to live data.

---

## What I need from you

Four HTTP endpoints and one WebSocket. All responses must be JSON.

---

### 1. Health check

```
GET /health
```

Returns `200 OK` with any body (even empty). The frontend uses this to detect whether the backend is reachable before attempting a full connection.

---

### 2. Tiles by hour

```
GET /tiles?hour={hour}
```

`hour` is an integer from `6` to `22` (6 AM to 10 PM).

Returns the stress tile data for that hour. Expected format — either a plain array:

```json
[
  {
    "h3_index": "8b29a1d71911fff",
    "als_score": 0.84,
    "context": "stationary",
    "noise_db": 82.0
  },
  ...
]
```

Or wrapped in an object — both work:

```json
{ "tiles": [ ... ] }
```

**Field reference:**

| Field | Type | Description |
|---|---|---|
| `h3_index` | string | H3 cell ID at resolution 11 |
| `als_score` | number | Anonymised stress score, 0.0–1.0 |
| `context` | string | `"stationary"`, `"walking"`, or `"transit_like"` |
| `noise_db` | number | Ambient noise in decibels |

> **H3 resolution must be 11.** The map renders at res 11 (~24m cells). Res 9 or 10 cells will not render correctly.

---

### 3. Hotspots

```
GET /hotspots
```

Returns the named stress hotspot locations. Expected format:

```json
[
  {
    "h3_index": "8b29a1d71911fff",
    "location_label": "Civic Center",
    "severity": "high",
    "als_score": 0.84,
    "noise_db": 82.0,
    "context": "stationary",
    "stressors": ["heat", "noise"]
  },
  ...
]
```

Or wrapped: `{ "hotspots": [ ... ] }`

**Field reference:**

| Field | Type | Description |
|---|---|---|
| `h3_index` | string | H3 cell ID at resolution 11 |
| `location_label` | string | Human-readable name shown in the panel |
| `severity` | string | `"low"`, `"medium"`, or `"high"` |
| `als_score` | number | 0.0–1.0 |
| `noise_db` | number | Decibels |
| `context` | string | `"stationary"`, `"walking"`, or `"transit_like"` |
| `stressors` | string[] | Any of: `"heat"`, `"noise"`, `"poor_crossing"`, `"congestion"`, `"poor_transit_flow"` |

---

### 4. Agents

```
GET /agents
```

Returns the current status of all agents in the system. Expected format:

```json
[
  {
    "id": "ingestion",
    "label": "Ingestion Agent",
    "status": "active",
    "message": "Receiving 47 packets/min"
  },
  ...
]
```

Or wrapped: `{ "agents": [ ... ] }`

**Field reference:**

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique agent identifier (e.g., `"ingestion"`) |
| `label` | string | Human-readable name (e.g., `"Ingestion Agent"`) |
| `status` | string | `"active"`, `"processing"`, `"idle"`, or `"error"` |
| `message` | string | Current status message |

This endpoint is optional. If not provided, the frontend falls back to mock agent statuses.

---

### 5. WebSocket — live tile stream

```
WS /ws/tiles
```

Push tile updates over WebSocket as they arrive from sensors. Each message should be a JSON string in the same format as the `/tiles` REST response — either a plain array or `{ "tiles": [...] }`.

The frontend will use WebSocket as the primary live feed. If the WebSocket is not available, it falls back to polling `/tiles?hour=` every 30 seconds automatically.

---

## Reference data

The synthetic dataset the frontend uses for demo mode is at:

```
superblock-ui/src/data/mockData.json
```

This is the exact shape the frontend was built against. Use it as a reference for field names, value ranges, and H3 cell IDs for the Downtown LA area.

---

## How the frontend handles your data

- If `/health` fails → stays in demo mode, no further calls made
- If `/health` succeeds but `/tiles` fails → falls back to mock data silently
- If WebSocket connects → live tiles override mock data in real time
- If WebSocket drops → automatically reconnects every 5 seconds
- If `/agents` succeeds → live agent statuses override mock data
- The header badge shows **LIVE** (green) when connected, **DEMO (offline)** (gray) when falling back

---

## Environment

The frontend expects your server at:

```
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws/tiles

VITE_API_PATH_HEALTH=/health
VITE_API_PATH_TILES=/tiles
VITE_API_PATH_HOTSPOTS=/hotspots
VITE_API_PATH_AGENTS=/agents
```

If your server runs on a different port or your routes have a prefix (e.g. `/api/v1/tiles`), just tell Karthik the values and he updates `.env.local` — no code changes needed.

---
