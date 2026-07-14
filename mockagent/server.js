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

// Ingestion status
app.get('/ingestion/status', (req, res) => {
  console.log('[ingestion] /ingestion/status called')
  const response = {
    packets_per_min: 47,
    sensors_online: 12,
    last_batch_id: 128,
    total_tiles: mockData.timeframes?.[0]?.tiles?.length ?? 0,
    status: 'active',
  }
  console.log('[ingestion] /ingestion/status response', response)
  res.json(response)
})

// Diagnosis
const STRESSOR_LABELS = {
  heat_exposure: 'Heat exposure',
  noise_pollution: 'Noise pollution',
  pedestrian_crowding: 'Pedestrian crowding',
  air_quality: 'Air quality',
  transit_delay: 'Transit delay',
}

app.get('/diagnosis', (req, res) => {
  const { h3_index } = req.query
  if (!h3_index) return res.status(400).json({ error: 'h3_index required' })

  console.log('[diagnosis] /diagnosis called for', h3_index)

  const hotspot = mockData.hotspots.find(h => h.h3_index === h3_index)

  if (hotspot) {
    const primary = hotspot.stressors[0] ?? 'urban_stress'
    const primaryLabel = STRESSOR_LABELS[primary] ?? primary
    res.json({
      h3_index,
      summary: `${hotspot.severity[0].toUpperCase() + hotspot.severity.slice(1)} stress at ${hotspot.location_label} — ${primaryLabel} dominant`,
      primary_stressor: primaryLabel,
      stressors: hotspot.stressors,
      als_score: hotspot.als_score,
      severity: hotspot.severity,
      recommended_action: hotspot.als_score >= 0.7
        ? 'Priority intervention recommended'
        : 'Monitor and assess further',
    })
  } else {
    res.json({
      h3_index,
      summary: 'Moderate stress detected — insufficient profile data',
      primary_stressor: 'Urban stress',
      stressors: ['urban_stress'],
      als_score: 0.5,
      severity: 'medium',
      recommended_action: 'Collect additional sensor data',
    })
  }
})

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

// Start HTTP server (localhost-only; demo mock, not for public bind)
const HOST = process.env.HOST || '127.0.0.1'
const server = app.listen(PORT, HOST, () => {
  console.log(`Mock server running on http://${HOST}:${PORT}`)
  console.log(`  GET  /health`)
  console.log(`  GET  /tiles`)
  console.log(`  GET  /hotspots`)
  console.log(`  GET  /agents`)
  console.log(`  GET  /ingestion/status`)
  console.log(`  GET  /diagnosis`)
  console.log(`  GET  /planner/interventions`)
  console.log(`  POST /simulate`)
})

// WebSocket for /ws/tiles (accept JSON only)
const wss = new WebSocket.Server({ server, path: '/ws/tiles' })
wss.on('connection', (ws) => {
  console.log('WS client connected')
  ws.on('message', (message) => {
    try {
      const text = message.toString()
      JSON.parse(text)
      ws.send(text)
    } catch {
      ws.send(JSON.stringify({ error: 'expected JSON message' }))
    }
  })
})
