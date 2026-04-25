# Superblock — Frontend Design Plan
**Owner:** Karthik | **Scope:** Item 2 (UI Only)

---

## Overview

Superblock is a real-time urban health dashboard that visualizes stress patterns across a city neighborhood using anonymized biometric data from Apple Watch users. The frontend is the primary judge-facing surface of the demo — everything judges see, click, and interact with lives here.

The UI is built as a single-page dashboard with no routing. A 3D map of Downtown LA forms the centerpiece, with H3 hexagonal tiles colored and elevated by stress intensity. Surrounding panels give judges the ability to inspect red zones, run what-if simulations, compare interventions, and watch the multi-agent system work in real time.

The design prioritizes demo reliability above all else. A complete synthetic dataset is bundled into the app so it runs fully offline if the backend is unavailable. Live data from Jeevika's backend is layered on top when available, with a silent fallback to mock on any failure. A visible Demo Mode toggle makes the data source transparent to judges.

---

## Module Summary

| # | Module | What It Does |
|---|---|---|
| 1 | Project Setup | Scaffolds the Vite + React app, installs all dependencies, configures Tailwind and environment |
| 2 | Layout Shell | Builds the full-page frame: header, two-column split (map + sidebar), tab panel, time slider footer |
| 3 | Mock Data Layer | Creates the synthetic DTLA dataset — tiles, hotspots, agents, interventions — that drives the demo |
| 4 | Zustand Store | Central state for all panels, selected hex, time index, simulation state, and live/demo mode |
| 5 | Map View | deck.gl H3HexagonLayer on Mapbox — colored and elevated tiles, click handler, hover tooltip |
| 6 | Time Slider | Scrubs through 24 hours of stress data, includes a play button to auto-replay the day |
| 7 | Agent Panel | Live status feed for all 6 agents (Ingestion → Narrator) with color-coded activity indicators |
| 8 | Hotspot Panel | Detail view for a clicked red zone — stressor labels, ALS score, noise level, context |
| 9 | Simulation Panel | Pick an intervention, trigger a simulation, display before/after ALS delta on result |
| 10 | Intervention Cards | Ranked list of all 4 interventions by Biological Relief Coefficient with a cost vs. impact chart |
| 11 | Live API Integration | Wires all panels to Jeevika's REST and WebSocket endpoints with mock fallback on failure |
| 12 | Demo Polish | Demo mode toggle, privacy badge, loading skeletons, auto-open judge demo state on first load |

---

## Tech Stack

| Layer | Tool | Notes |
|---|---|---|
| Framework | React + Vite | Fast setup, no SSR needed for a dashboard |
| Map | Mapbox GL JS | Free tier (50k loads/month), dark basemap, polished out of the box |
| Hex Layer | deck.gl H3HexagonLayer | Native H3 tile rendering with elevation and color gradients |
| Styling | Tailwind CSS | Utility-first, dark theme, no design system overhead |
| Components | shadcn/ui | Copy-paste components — Card, Badge, Tabs, Slider, Button |
| Charts | Recharts | Cost vs. impact bar chart for intervention comparison |
| State | Zustand | Single lightweight store, no boilerplate |
| Deployment | Vercel | Free tier, instant deploy from GitHub push |

---

## Build Order

| # | Module | Depends On |
|---|---|---|
| 1 | Project Setup | — |
| 2 | Layout Shell | 1 |
| 3 | Mock Data Layer | 1 |
| 4 | Zustand Store | 3 |
| 5 | Map View | 3, 4 |
| 6 | Time Slider | 4, 5 |
| 7 | Agent Panel | 4 |
| 8 | Hotspot Panel | 4, 5 |
| 9 | Simulation Panel | 4, 8 |
| 10 | Intervention Cards | 4, 9 |
| 11 | Live API Integration | All |
| 12 | Demo Polish | All |

---

## Folder Structure

```
superblock-ui/
├── public/
│   └── mock/
│       └── mockData.json          # synthetic day-long demo dataset
├── src/
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── AppLayout.tsx
│   │   ├── map/
│   │   │   └── MapView.tsx
│   │   ├── panels/
│   │   │   ├── AgentPanel.tsx
│   │   │   ├── HotspotPanel.tsx
│   │   │   ├── SimPanel.tsx
│   │   │   └── InterventionCards.tsx
│   │   └── controls/
│   │       └── TimeSlider.tsx
│   ├── store/
│   │   └── useStore.ts            # single Zustand store
│   ├── data/
│   │   └── mock.ts                # typed mock data loader
│   ├── lib/
│   │   ├── api.ts                 # all backend API calls
│   │   ├── colorScale.ts          # ALS score → hex color
│   │   └── constants.ts           # H3 res, map center, agent list
│   ├── types/
│   │   └── index.ts               # all shared TypeScript types
│   ├── App.tsx
│   └── main.tsx
├── .env.local                     # VITE_MAPBOX_TOKEN
├── index.html
├── tailwind.config.ts
├── vite.config.ts
└── package.json
```

---

## Module 1 — Project Setup

### Commands
```bash
npm create vite@latest superblock-ui -- --template react-ts
cd superblock-ui
npm install

# Map
npm install mapbox-gl @deck.gl/react @deck.gl/layers @deck.gl/geo-layers react-map-gl h3-js

# UI
npm install tailwindcss @tailwindcss/vite
npm install recharts
npm install zustand

# shadcn
npx shadcn@latest init
npx shadcn@latest add card badge button tabs separator slider
```

### Environment
```
# .env.local
VITE_MAPBOX_TOKEN=pk.eyJ1...   # free Mapbox account, no credit card
```

### tailwind.config.ts
- Dark theme as default (dashboards read better dark)
- Content paths: `./src/**/*.{ts,tsx}`

---

## Module 2 — Layout Shell

### AppLayout.tsx
```
┌──────────────────────────────────────────────────────┐
│ Header (h-14)                                        │
├─────────────────────────────┬────────────────────────┤
│                             │                        │
│  MapView                    │  Sidebar               │
│  flex-1 h-full              │  w-96 h-full           │
│                             │                        │
├─────────────────────────────┴────────────────────────┤
│ TimeSlider (h-16)                                    │
└──────────────────────────────────────────────────────┘
```

### Header.tsx — Elements
- Left: `SuperBlock` wordmark + subtitle "Urban Nervous System"
- Center: `● LIVE` green pulse indicator OR `◉ DEMO` amber badge
- Right: Privacy badge — "Raw biometrics stay on-device 🔒"
- Right: Demo Mode toggle (Switch from shadcn)

### Sidebar.tsx — Three Tabs
```
[Agents]  [Hotspot]  [Simulation]
```
- Default tab: Agents
- Hotspot tab activates automatically when a hex is clicked on the map
- Simulation tab activates when "Run Simulation" is pressed

---

## Module 3 — Mock Data Layer

### public/mock/mockData.json — Schema

```json
{
  "neighborhood": "Downtown LA",
  "center": [-118.2437, 34.0522],
  "timeframes": [
    {
      "label": "6:00 AM",
      "time_index": 0,
      "tiles": [
        {
          "h3_index": "8929a0c54ffffff",
          "als_score": 0.21,
          "context": "walking",
          "noise_db": 54.0
        }
      ]
    }
  ],
  "hotspots": [
    {
      "h3_index": "8929a0c54ffffff",
      "stressors": ["heat", "noise"],
      "severity": "high",
      "als_score": 0.84,
      "noise_db": 82.0,
      "context": "stationary",
      "location_label": "5th & Grand"
    }
  ],
  "agents": [
    { "id": "ingestion", "label": "Ingestion Agent", "status": "active", "message": "Receiving 47 packets/min" },
    { "id": "mapping",   "label": "Mapping Agent",   "status": "active", "message": "3 red zones detected" },
    { "id": "diagnosis", "label": "Diagnosis Agent", "status": "idle",   "message": "Waiting for hotspot query" },
    { "id": "simulation","label": "Simulation Agent","status": "idle",   "message": "Ready" },
    { "id": "planner",   "label": "Planner Agent",   "status": "idle",   "message": "Ready" },
    { "id": "narrator",  "label": "Narrator Agent",  "status": "idle",   "message": "Ready" }
  ],
  "interventions": [
    {
      "id": "shade_canopy",
      "label": "Shade Canopy",
      "icon": "🌿",
      "predicted_als_delta": -0.24,
      "estimated_cost_usd": 8500,
      "relief_coefficient": 0.0000282,
      "description": "Install shade sails along 5th St reducing surface temp by 4°C"
    },
    {
      "id": "longer_walk_signal",
      "label": "Longer Walk Signal",
      "icon": "🚦",
      "predicted_als_delta": -0.14,
      "estimated_cost_usd": 1200,
      "relief_coefficient": 0.0001167,
      "description": "Extend pedestrian crossing time by 15s at 5th & Grand"
    },
    {
      "id": "parklet",
      "label": "Parklet",
      "icon": "🪑",
      "predicted_als_delta": -0.18,
      "estimated_cost_usd": 12000,
      "relief_coefficient": 0.000015,
      "description": "Install resting parklet with seating and greenery"
    },
    {
      "id": "pedestrian_bridge",
      "label": "Pedestrian Bridge",
      "icon": "🌉",
      "predicted_als_delta": -0.31,
      "estimated_cost_usd": 95000,
      "relief_coefficient": 0.00000326,
      "description": "Grade-separated crossing eliminating vehicle conflict zone"
    }
  ]
}
```

### data/mock.ts
- Exports typed loader functions
- `getMockTilesAtIndex(timeIndex: number): Tile[]`
- `getMockHotspot(h3Index: string): Hotspot | null`
- `getMockAgents(): Agent[]`
- `getMockInterventions(): Intervention[]`

---

## Module 4 — Zustand Store

### store/useStore.ts — State Shape

```ts
interface StoreState {
  // Connection
  isLive: boolean
  isDemoMode: boolean

  // Time
  timeIndex: number          // 0–23 (hours of day)
  setTimeIndex: (i: number) => void

  // Map
  tiles: Tile[]
  selectedHexId: string | null
  setSelectedHex: (id: string | null) => void

  // Panels
  activeTab: 'agents' | 'hotspot' | 'simulation'
  setActiveTab: (tab: ActiveTab) => void

  // Agents
  agents: Agent[]

  // Hotspot
  selectedHotspot: Hotspot | null

  // Simulation
  simRunning: boolean
  simResult: SimResult | null
  runSimulation: (interventionId: string) => void

  // Interventions
  interventions: Intervention[]
  rankedInterventions: Intervention[]

  // Actions
  toggleDemoMode: () => void
}
```

### Key behaviors
- `setSelectedHex` → also sets `activeTab` to `'hotspot'` and loads hotspot data
- `runSimulation` → sets `simRunning: true`, sets `activeTab` to `'simulation'`, resolves after 1.5s (mock delay for demo effect)
- `timeIndex` change → reloads `tiles` from mock data for that hour

---

## Module 5 — Map View

### MapView.tsx

```
React component wrapping DeckGL over react-map-gl StaticMap
```

**Layers (in order):**
1. `H3HexagonLayer` — all tiles, colored by ALS score, elevated by ALS score
2. `H3HexagonLayer` (red zones only) — pulsing outline for tiles where `als_score > 0.7`

**H3HexagonLayer config:**
```ts
{
  id: 'stress-layer',
  data: tiles,
  getHexagon: d => d.h3_index,
  getFillColor: d => alsToColor(d.als_score),   // from colorScale.ts
  getElevation: d => d.als_score * 400,          // height = stress intensity
  elevationScale: 1,
  extruded: true,
  pickable: true,
  onClick: ({ object }) => setSelectedHex(object.h3_index)
}
```

**colorScale.ts:**
```
0.0 – 0.3  →  [34, 197, 94]    green
0.3 – 0.5  →  [234, 179, 8]    yellow
0.5 – 0.7  →  [249, 115, 22]   orange
0.7 – 1.0  →  [239, 68, 68]    red
```

**Mapbox style:** `mapbox://styles/mapbox/dark-v11` (free, no extra config)

**Map center and zoom:** Centered on DTLA — `[-118.2437, 34.0522]`, zoom 14

**Tooltip:** Small floating card showing `ALS: 0.84 | Noise: 82dB | Context: stationary` on hover

---

## Module 6 — Time Slider

### TimeSlider.tsx

- shadcn Slider component, range 0–23 (hours)
- Labels: `6 AM`, `9 AM`, `12 PM`, `3 PM`, `6 PM`, `9 PM` evenly spaced
- On change → `setTimeIndex(value)` in store
- Play button → auto-increments timeIndex every 800ms (shows stress patterns evolving)
- Shows current time label: `2:00 PM`

---

## Module 7 — Agent Panel

### AgentPanel.tsx

Renders inside the Agents tab. List of 6 agents.

**Each agent row:**
```
● [icon]  Ingestion Agent
          Receiving 47 packets/min
          ──────────────────────  [timestamp]
```

**Status indicator colors:**
- `active` → green pulsing dot
- `processing` → amber spinning dot
- `idle` → gray dot
- `error` → red dot

**For demo:** cycle agent statuses in sequence when the map is in live mode (ingestion active → mapping active → diagnosis active → etc.) using a setInterval in the store.

---

## Module 8 — Hotspot Panel

### HotspotPanel.tsx

Renders inside the Hotspot tab. Activated when a hex is clicked.

**Empty state:** "Click a red zone on the map to inspect it"

**Populated state:**
```
📍 5th & Grand
H3: 8929a0c54ffffff

Stress Score
[████████░░] 0.84 / 1.0   HIGH

Likely Stressors
[🌡 Heat] [🔊 Noise] [🚶 Poor Crossing]

Context: Stationary
Noise: 82 dB

[Run Simulation →]   button
```

**"Run Simulation" button** → sets `activeTab` to `'simulation'`, triggers `runSimulation` prep

---

## Module 9 — Simulation Panel

### SimPanel.tsx

Renders inside the Simulation tab.

**Step 1 — Pick Intervention (before run):**
- 4 cards in a 2×2 grid
- Each card: icon, label, cost, predicted ALS delta
- Selected card highlighted with border
- `Run Simulation` button at bottom

**Step 2 — Running (1.5s):**
- Spinner + `Simulating intervention...`
- Map briefly shows ghost overlay on selected hex

**Step 3 — Result:**
```
Shade Canopy — Result

Before:  [████████░░] 0.84
After:   [█████░░░░░] 0.60
Delta:   -0.24  (-29%)

See all interventions ranked →  [link to tab or scroll]
```

---

## Module 10 — Intervention Cards

### InterventionCards.tsx

Rendered below SimPanel result or as its own section.

**Ranked list** (sorted by `relief_coefficient` desc):

```
Rank  Intervention          ALS Δ    Cost      BRC
 1    Longer Walk Signal    -0.14    $1,200    ████████ 0.000117
 2    Shade Canopy          -0.24    $8,500    ████░░   0.0000282
 3    Parklet               -0.18    $12,000   ███░░    0.000015
 4    Pedestrian Bridge     -0.31    $95,000   █░░░░    0.00000326
```

**Recharts BarChart** below the list:
- X axis: intervention labels
- Two bars per group: ALS reduction (blue) and cost normalized (amber)
- This is the "cost vs impact" visual for judges

---

## Module 11 — Live API Integration

### lib/api.ts — Endpoints to wire up

All calls fall back silently to mock data if the request fails or times out (2s timeout).

```ts
// Jeevika's endpoints
GET  /api/tiles?time_index={n}       → Tile[]
GET  /api/hotspot?h3_index={id}      → Hotspot
POST /api/simulate                   → SimResult
     body: { h3_index, intervention_id }
GET  /api/agents                     → Agent[]

// WebSocket
WS   /ws/tiles                       → stream of Tile updates
```

### Fallback logic (in store)

```ts
async function loadTiles(timeIndex: number) {
  try {
    const res = await fetchWithTimeout(`/api/tiles?time_index=${timeIndex}`, 2000)
    set({ tiles: await res.json(), isLive: true })
  } catch {
    set({ tiles: getMockTilesAtIndex(timeIndex), isLive: false })
  }
}
```

### WebSocket (when live)

```ts
const ws = new WebSocket(WS_URL)
ws.onmessage = (e) => {
  const tile: Tile = JSON.parse(e.data)
  // update only the changed tile in the store
  set(state => ({
    tiles: state.tiles.map(t => t.h3_index === tile.h3_index ? tile : t)
  }))
}
ws.onerror = () => set({ isLive: false }) // silent fallback to mock
```

---

## Module 12 — Demo Polish

### Demo Mode Toggle (Header)
- When ON: loads full mock dataset, disables API calls
- Shows `◉ DEMO MODE` badge in amber
- Useful when demoing offline or when backend is unstable

### Privacy Badge (Header)
Small persistent element:
```
🔒 Raw biometrics: on-device only
   ALS score · context · H3 tile
```

### Loading States
- Map skeleton while tiles load (semi-transparent overlay)
- Skeleton cards in panels while data resolves
- All skeletons resolve in <300ms from mock

### Judge Demo Checklist (runtime)
On first load in demo mode, auto:
1. Set timeIndex to 14 (2 PM — peak stress hour)
2. Pre-select the highest ALS hex on the map
3. Open Hotspot tab
4. This gives judges immediate visual payoff before any interaction

### Vercel Deployment
```bash
npm run build
# push to GitHub → connect repo to Vercel → auto-deploy
# set VITE_MAPBOX_TOKEN in Vercel environment variables
```

---

## TypeScript Types

```ts
// types/index.ts

export interface Tile {
  h3_index: string
  als_score: number          // 0.0 – 1.0
  context: 'stationary' | 'walking' | 'transit_like'
  noise_db: number
}

export interface Hotspot {
  h3_index: string
  stressors: string[]
  severity: 'low' | 'medium' | 'high'
  als_score: number
  noise_db: number
  context: string
  location_label: string
}

export interface Agent {
  id: string
  label: string
  status: 'active' | 'processing' | 'idle' | 'error'
  message: string
  timestamp?: string
}

export interface Intervention {
  id: string
  label: string
  icon: string
  predicted_als_delta: number     // negative = improvement
  estimated_cost_usd: number
  relief_coefficient: number      // ALS reduction per dollar
  description: string
}

export interface SimResult {
  intervention_id: string
  h3_index: string
  als_before: number
  als_after: number
  als_delta: number
  percent_reduction: number
}
```

---

## API Contract (agree with Jeevika)

Karthik needs these four contracts locked early. Everything else is internal.

| Contract | Field | Type | Notes |
|---|---|---|---|
| Tile | `h3_index` | string | H3 Res 9 |
| Tile | `als_score` | float 0–1 | core stress value |
| Tile | `context` | enum string | stationary, walking, transit_like |
| Tile | `noise_db` | float | ambient noise |
| Hotspot | `stressors` | string[] | labels from Diagnosis Agent |
| SimResult | `als_before` / `als_after` | float | for before/after display |
| Agent | `status` | enum string | active, processing, idle, error |
| Agent | `message` | string | one-line status message |

---

## What Karthik Does NOT Build

- Agent logic, prompts, or orchestration (Item 3)
- Stress score computation or ALS pipeline (Item 1)
- Apple Watch data ingestion (Item 1)
- WebSocket server (Item 1)
- ASI:One chat protocol (Item 3)
- Agent Almanac registration (Item 3)
