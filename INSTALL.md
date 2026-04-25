# Superblock UI — Installation Guide
**Project:** Superblock Frontend (`superblock-ui`)
**Last updated:** Module 1 — Project Setup

---

## Prerequisites

| Tool | Version | Install |
|---|---|---|
| Node.js | 22 LTS | https://nodejs.org (download LTS installer) |
| npm | ships with Node | included |
| Git | any | https://git-scm.com |
| Mapbox account | free | https://account.mapbox.com/auth/signup |

---

## Mac Setup (New Machine)

### Step 1 — Install Node.js

Option A — Direct download (simplest):
- Go to https://nodejs.org → download the macOS LTS `.pkg` → run installer

Option B — Homebrew (recommended if you already use Homebrew):
```bash
brew install node@22
```

Verify:
```bash
node --version   # should show v22.x.x
npm --version    # should show 11.x.x
```

---

### Step 2 — Clone or copy the project

```bash
cd ~/your-projects-folder
# copy the SuperBlock folder here, or clone from repo
```

---

### Step 3 — Install dependencies

```bash
cd SuperBlock/superblock-ui
npm install
```

This installs everything from `package.json` — no individual install commands needed.

---

### Step 4 — Get a Mapbox token

1. Sign up free at https://account.mapbox.com/auth/signup
2. Go to **Account → Tokens → Create a token**
3. Use the default public token (starts with `pk.eyJ1...`)
4. No credit card required for the free tier (50,000 map loads/month)

---

### Step 5 — Configure environment

Create a file called `.env.local` inside `superblock-ui/`:

```bash
cd SuperBlock/superblock-ui
cp .env.local.example .env.local   # if example exists, or create manually
```

Edit `.env.local`:
```
VITE_MAPBOX_TOKEN=pk.eyJ1...your_token_here
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws/tiles
```

> `.env.local` is never committed to git. Each machine needs its own copy.

---

### Step 6 — Run the dev server

```bash
npm run dev
```

Open http://localhost:5173 in your browser.

---

### Step 7 — Build for production (Vercel deploy)

```bash
npm run build
```

Output goes to `dist/`. Vercel picks this up automatically on push.

---

## Vercel Deployment (Mac or Windows)

1. Push `superblock-ui/` to a GitHub repo
2. Go to https://vercel.com → New Project → import the repo
3. Set root directory to `superblock-ui`
4. Add environment variable: `VITE_MAPBOX_TOKEN` = your token
5. Deploy — Vercel auto-deploys on every push to main

---

## Installed Packages Reference

These are already in `package.json`. `npm install` handles all of them.

| Package | Purpose |
|---|---|
| `react` + `react-dom` | UI framework |
| `vite` + `@vitejs/plugin-react` | Dev server and bundler |
| `typescript` | Type safety |
| `tailwindcss` + `@tailwindcss/vite` | Styling |
| `mapbox-gl` | Map rendering |
| `react-map-gl` | React wrapper for Mapbox |
| `@deck.gl/react` | deck.gl React integration |
| `@deck.gl/layers` | Core deck.gl layers |
| `@deck.gl/geo-layers` | H3HexagonLayer |
| `h3-js` | H3 hex grid utilities |
| `zustand` | State management |
| `recharts` | Charts for intervention comparison |
| `@types/node` | TypeScript types for Node built-ins |

---

## Troubleshooting

**`npm` not found after installing Node on Mac:**
```bash
export PATH="/usr/local/bin:$PATH"   # Intel Mac
export PATH="/opt/homebrew/bin:$PATH"  # Apple Silicon Mac
```
Add to your `~/.zshrc` to make it permanent.

**Map not showing / blank map:**
- Check that `VITE_MAPBOX_TOKEN` is set in `.env.local`
- Token must start with `pk.eyJ1`
- Restart dev server after editing `.env.local`

**Port 5173 already in use:**
```bash
npm run dev -- --port 3000
```

**TypeScript path alias errors (`@/` imports not resolving):**
- Ensure `tsconfig.app.json` has `"ignoreDeprecations": "6.0"` and the `paths` config
- Restart your IDE / TypeScript server
