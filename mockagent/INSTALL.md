# Mock Agent Setup Guide

This guide helps you set up the mock agent for the Superblock project. The mock agent simulates backend endpoints for testing the frontend without a real backend.

## Prerequisites
- **Node.js** (version 16 or higher): Download from [nodejs.org](https://nodejs.org/).
- **Git** (optional, for cloning the repo).
- The Superblock project files (including `mockagent/` and `superblock-ui/`).

## Installation Steps

### 1. Navigate to the Mock Agent Directory
```bash
cd path/to/Superblock/mockagent
```
Replace `path/to/Superblock` with your actual project path.

### 2. Install Dependencies
```bash
npm install
```
This installs Express, CORS, and WebSocket libraries. It may take a few minutes.

### 3. Start the Mock Server
```bash
npm start
```
- The server runs on `http://localhost:8000`.
- You should see: `Mock server running on http://localhost:8000`.
- Keep this terminal open. Press Ctrl+C to stop.

### 4. Verify Endpoints (Optional)
Test the endpoints with curl (or use Postman):
```bash
# Health check
curl http://localhost:8000/health

# Tiles for hour 6
curl "http://localhost:8000/tiles?hour=6"

# Hotspots
curl http://localhost:8000/hotspots

# Agents
curl http://localhost:8000/agents

# WebSocket (install wscat first: npm install -g wscat)
wscat -c ws://localhost:8000/ws/tiles
```

Expected responses:
- `/health`: `"OK"`
- `/tiles`: JSON array of tiles.
- `/hotspots`: JSON array of hotspots.
- `/agents`: JSON array of agents.
- WS: Connects and echoes messages.

## Running the Full App

### Start the Frontend Separately
In a new terminal:
```bash
cd ../superblock-ui  # From mockserver/
npm install  # If not done
npm run dev
```
- Opens at `http://localhost:5173`.
- Toggle off "Demo Mode" in the header to connect to the mock server.
- Header should show "LIVE" if connected.

### Troubleshooting
- **Port Conflict**: If 8000 is in use, edit `server.js` and change `const PORT = 8000` to another port (e.g., 3001). Update `superblock-ui/.env.local` accordingly.
- **CORS Errors**: The server includes CORS headers. If issues persist, ensure both are on localhost.
- **Dependencies Fail**: Delete `node_modules` and `package-lock.json`, then `npm install`.
- **Server Won't Start**: Check Node.js version with `node -v`. Ensure `mockData.json` exists in `../superblock-ui/src/data/`.
- **Frontend Won't Connect**: Check browser console for errors. Ensure `.env.local` has `VITE_API_BASE_URL=http://localhost:8000`.

## What's Included
- **Endpoints**: Simulates `/health`, `/tiles`, `/hotspots`, `/agents`, `/ws/tiles`.
- **Data Source**: Pulls from `../superblock-ui/src/data/mockData.json`.
- **CORS**: Enabled for cross-origin requests from the frontend.

For issues, check the project README or contact the team. Happy coding!