# Superblock UI — Installation Guide

**Repo:** https://github.com/KarthikSubramanian07/Superblock.git  
**App folder:** `superblock-ui/`

---

## Prerequisites

| Tool | Version | Install |
|---|---|---|
| Node.js | 22 LTS | https://nodejs.org — download LTS installer |
| npm | ships with Node | included |
| Git | any | https://git-scm.com |
| VS Code | any | https://code.visualstudio.com |

---

## Step 1 — Install Node.js

### Mac
Option A — Direct download (simplest):
- Go to https://nodejs.org → download the macOS LTS `.pkg` → run installer

Option B — Homebrew:
```bash
brew install node@22
```

### Windows
- Go to https://nodejs.org → download the Windows LTS `.msi` → run installer
- Make sure **"Add to PATH"** is checked during installation

### Verify (both platforms)
```bash
node --version   # v22.x.x
npm --version    # 11.x.x
```

---

## Step 2 — Clone the repo

### Mac
```bash
cd ~/Documents          # or any folder you prefer
git clone https://github.com/KarthikSubramanian07/Superblock.git
cd Superblock
```

### Windows (Command Prompt or PowerShell)
```powershell
cd C:\Users\YourName\Documents
git clone https://github.com/KarthikSubramanian07/Superblock.git
cd Superblock
```

### Open in VS Code
```bash
code superblock-ui
```
Or: **File → Open Folder** → select the `superblock-ui` folder.

---

## Step 4 — Install dependencies

```bash
cd superblock-ui
npm install
```

---

## Step 5 — Create the environment file

Create a file named `.env.local` inside the `superblock-ui/` folder.

### Mac
```bash
touch superblock-ui/.env.local
```

### Windows (PowerShell)
```powershell
New-Item superblock-ui\.env.local -ItemType File
```

Open `.env.local` in VS Code and paste:

```
VITE_MAPBOX_TOKEN=<token shared by Karthik>

# Backend server
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws/tiles

# API endpoint paths (change if backend uses different routes)
VITE_API_PATH_HEALTH=/health
VITE_API_PATH_TILES=/tiles
VITE_API_PATH_HOTSPOTS=/hotspots

# Connection tuning (optional — defaults shown)
VITE_POLL_INTERVAL_MS=30000
VITE_WS_RECONNECT_MS=5000
VITE_HEALTH_TIMEOUT_MS=2000
```

> `.env.local` is excluded from git. Every machine needs its own copy.

---

## Step 6 — Run the dev server

```bash
cd superblock-ui
npm run dev
```

Open http://localhost:5173 in your browser.

The app opens with:
- Stress zone map of Downtown LA centred at 2 PM (peak stress)
- Civic Center hotspot auto-selected after 1 second
- Agents panel showing live cycling status
- Time slider at the bottom to scrub through the day

---

## Config files you can edit without touching component code

| File | What it controls |
|---|---|
| `src/data/agentMessages.ts` | Rotating status text under each agent |
| `src/data/agentHelp.ts` | Tooltip help text next to each agent |
| `src/data/interventions.config.ts` | Intervention labels, icons, costs, ALS deltas |
| `src/lib/constants.ts` | Map centre, zoom level, ALS thresholds |

---

## Packages reference

All installed via `npm install` — no manual steps.

| Package | Purpose |
|---|---|
| `react` + `react-dom` | UI framework |
| `vite` + `@vitejs/plugin-react` | Dev server and bundler |
| `typescript` | Type safety |
| `tailwindcss` + `@tailwindcss/vite` | Utility-first styling |
| `mapbox-gl` + `react-map-gl` | Map rendering |
| `@deck.gl/react` + `@deck.gl/layers` | Overlay layer system |
| `@deck.gl/geo-layers` | H3HexagonLayer |
| `h3-js` | H3 hex grid maths |
| `zustand` | Lightweight state management |
| `recharts` | Cost vs. impact bar chart |

---

## Troubleshooting

**Map is blank / token error:**
- Confirm `VITE_MAPBOX_TOKEN` in `.env.local` is the token from Karthik
- Restart the dev server after editing `.env.local`

**`npm` not found on Mac after install:**
```bash
export PATH="/usr/local/bin:$PATH"    # Intel Mac
export PATH="/opt/homebrew/bin:$PATH" # Apple Silicon Mac
```
Add to `~/.zshrc` to make permanent, then run `source ~/.zshrc`.

**`npm` not found on Windows:**
- Re-run the Node installer and ensure **"Add to PATH"** is ticked
- Or add `C:\Program Files\nodejs` manually to System → Environment Variables → PATH

**Port 5173 already in use:**
```bash
npm run dev -- --port 3000
```

**`@/` import errors in VS Code:**
- Run **TypeScript: Restart TS Server** from the VS Code command palette (Ctrl+Shift+P / Cmd+Shift+P)

**Windows line-ending warnings from Git:**
These are harmless — Git normalising LF ↔ CRLF. Ignore them.
