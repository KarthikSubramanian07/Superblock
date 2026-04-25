const express = require('express')
const cors = require('cors')
const WebSocket = require('ws')
const mockData = require('../superblock-ui/src/data/mockData.json')  // Path to your mockData.json

const app = express()
app.use(cors())  // Enable CORS for all routes
app.use(express.json())
const PORT = 8000

// Health check
app.get('/health', (req, res) => res.json('OK'))

// Tiles by hour
app.get('/tiles', (req, res) => {
  const hour = parseInt(req.query.hour) || 6
  const tiles = mockData.timeframes.find(t => t.time_index === hour)?.tiles || []
  res.json(tiles)
})

// Hotspots
app.get('/hotspots', (req, res) => res.json(mockData.hotspots))

// Agents
app.get('/agents', (req, res) => res.json(mockData.agents))

// Planner interventions — ranked by relief_coefficient desc
app.get('/planner/interventions', (req, res) => {
  const interventions = (mockData.interventions ?? [])
    .slice()
    .sort((a, b) => b.relief_coefficient - a.relief_coefficient)
  console.log('[planner] /planner/interventions called — returning', interventions.length, 'interventions')
  res.json(interventions)
})

// Simulation
app.post('/simulate', (req, res) => {
  const { h3_index, intervention_id, als_before } = req.body || {}
  console.log('[mockagent] /simulate called', { h3_index, intervention_id, als_before })

  if (!h3_index || !intervention_id || typeof als_before !== 'number') {
    console.log('[mockagent] /simulate missing payload')
    return res.status(400).json({ error: 'Missing simulation payload' })
  }

  const hotspot = mockData.hotspots.find(h => h.h3_index === h3_index)
  const intervention = mockData.interventions?.find(i => i.id === intervention_id)
  if (!intervention) {
    console.log('[mockagent] /simulate intervention not found', { intervention_id })
    return res.status(404).json({ error: 'Intervention not found' })
  }

  const beforeValue = hotspot?.als_score ?? als_before
  const afterValue = Math.max(0.01, beforeValue + intervention.predicted_als_delta)
  const delta = Math.round((afterValue - beforeValue) * 100) / 100
  const percentReduction = Math.round((Math.abs(delta) / beforeValue) * 100)
  const response = {
    intervention_id,
    h3_index,
    als_before: Math.round(beforeValue * 100) / 100,
    als_after: Math.round(afterValue * 100) / 100,
    als_delta: delta,
    percent_reduction: percentReduction,
  }

  console.log('[mockagent] /simulate response', response)
  res.json(response)
})

// Start HTTP server
const server = app.listen(PORT, () => {
  console.log(`Mock server running on http://localhost:${PORT}`)
  console.log(`  GET  /health`)
  console.log(`  GET  /tiles`)
  console.log(`  GET  /hotspots`)
  console.log(`  GET  /agents`)
  console.log(`  GET  /planner/interventions`)
  console.log(`  POST /simulate`)
})

// WebSocket for /ws/tiles (basic echo for testing)
const wss = new WebSocket.Server({ server, path: '/ws/tiles' })
wss.on('connection', (ws) => {
  console.log('WS client connected')
  ws.on('message', (message) => ws.send(message))  // Echo for now
})