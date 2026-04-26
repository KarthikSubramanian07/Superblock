// Generates src/data/mockData.json using real H3 indices for DTLA
import { latLngToCell, gridDisk, gridDistance } from 'h3-js'
import { writeFileSync, mkdirSync } from 'fs'
import { fileURLToPath } from 'url'
import { dirname, join } from 'path'

const __dirname = dirname(fileURLToPath(import.meta.url))

const CENTER_LAT = 34.0522
const CENTER_LNG = -118.2437
const H3_RES = 11       // fine-grain cells (~24m edge) for smooth organic look
const GRID_RADIUS = 30  // ~2791 cells covering ~2.7km radius

const centerCell = latLngToCell(CENTER_LAT, CENTER_LNG, H3_RES)
const cells = gridDisk(centerCell, GRID_RADIUS)

// Three stress hotspot centres within DTLA
const HOTSPOT_LATLNGS = [
  [34.056, -118.247],  // Civic Center / Bunker Hill
  [34.049, -118.238],  // Little Tokyo
  [34.042, -118.251],  // Jewelry District
]
const hotspotCells = HOTSPOT_LATLNGS.map(([lat, lng]) => latLngToCell(lat, lng, H3_RES))

// Precompute min grid-distance to any hotspot for every cell (once, reused per timeframe)
console.log('Computing distances...')
const minDistances = cells.map(cell => {
  let minDist = 999
  for (const hc of hotspotCells) {
    try {
      const d = gridDistance(cell, hc)
      if (d < minDist) minDist = d
    } catch { /* cells in different base cells */ }
  }
  return minDist
})

const HOURLY_STRESS = {
  6: 0.15, 7: 0.25, 8: 0.45, 9: 0.55,
  10: 0.50, 11: 0.60, 12: 0.65, 13: 0.70,
  14: 0.85, 15: 0.80, 16: 0.75, 17: 0.70,
  18: 0.65, 19: 0.55, 20: 0.45, 21: 0.35, 22: 0.25,
}

const CONTEXTS = ['stationary', 'walking', 'transit_like']

function seeded(seed) {
  const x = Math.sin(seed + 1) * 10000
  return x - Math.floor(x)
}

function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)) }

// --- Timeframes ---
const timeframes = []
for (let hour = 6; hour <= 22; hour++) {
  const factor = HOURLY_STRESS[hour]
  const label = hour < 12 ? `${hour}:00 AM` : hour === 12 ? '12:00 PM' : `${hour - 12}:00 PM`

  const tiles = cells.map((cell, i) => {
    const dist = minDistances[i]
    const decay = Math.exp(-dist * 0.10)   // smooth exponential falloff from hotspots
    const base  = 0.10 + decay * 0.85 * factor
    const seed  = i * 100 + hour
    const noise = (seeded(seed) - 0.5) * 0.04
    const als   = clamp(base + noise, 0.05, 0.95)

    const noiseBase = decay > 0.6 ? 68 : 48
    const noise_db  = clamp(noiseBase + seeded(seed + 300) * 15 + factor * 12, 38, 92)

    return {
      h3_index:  cell,
      als_score: Math.round(als * 100) / 100,
      context:   CONTEXTS[Math.floor(seeded(seed + 200) * 3)],
      noise_db:  Math.round(noise_db * 10) / 10,
    }
  })

  timeframes.push({ label, time_index: hour - 6, hour, tiles })
}

// --- Hotspots (use cell nearest to each hotspot lat/lng) ---
const hotspots = hotspotCells.map((hc, i) => {
  const labels     = ['Civic Center', 'Little Tokyo', 'Jewelry District']
  const stressors  = [['heat', 'noise'], ['poor_crossing', 'congestion'], ['heat', 'poor_transit_flow']]
  const severities = ['high', 'high', 'medium']
  const alsScores  = [0.84, 0.79, 0.68]
  const noises     = [82.0, 76.5, 69.0]
  const cell       = cells.find(c => c === hc) ?? cells[i * 120]
  return {
    h3_index:       cell,
    stressors:      stressors[i],
    severity:       severities[i],
    als_score:      alsScores[i],
    noise_db:       noises[i],
    context:        'stationary',
    location_label: labels[i],
  }
})

// --- Agents ---
const agents = [
  { id: 'ingestion',  label: 'Ingestion Agent',  status: 'active',  message: 'Receiving 47 packets/min' },
  { id: 'mapping',    label: 'Mapping Agent',    status: 'active',  message: '3 red zones detected' },
  { id: 'diagnosis',  label: 'Diagnosis Agent',  status: 'idle',    message: 'Waiting for hotspot query' },
  { id: 'simulation', label: 'Simulation Agent', status: 'idle',    message: 'Ready' },
  { id: 'planner',    label: 'Planner Agent',    status: 'idle',    message: 'Ready' },
  { id: 'narrator',   label: 'Narrator Agent',   status: 'idle',    message: 'Ready' },
]

// --- Interventions ---
const interventions = [
  { id: 'shade_canopy',       label: 'Shade Canopy',       icon: '🌿', predicted_als_delta: -0.24, estimated_cost_usd: 8500,  relief_coefficient: 0.0000282,  description: 'Install shade sails along 5th St reducing surface temp by 4°C' },
  { id: 'longer_walk_signal', label: 'Longer Walk Signal', icon: '🚦', predicted_als_delta: -0.14, estimated_cost_usd: 1200,  relief_coefficient: 0.0001167,  description: 'Extend pedestrian crossing time by 15s at 5th & Grand' },
  { id: 'parklet',            label: 'Parklet',            icon: '🪑', predicted_als_delta: -0.18, estimated_cost_usd: 12000, relief_coefficient: 0.000015,   description: 'Install resting parklet with seating and greenery' },
  { id: 'pedestrian_bridge',  label: 'Pedestrian Bridge',  icon: '🌉', predicted_als_delta: -0.31, estimated_cost_usd: 95000, relief_coefficient: 0.00000326, description: 'Grade-separated crossing eliminating vehicle conflict zone' },
]

// --- Write ---
const outDir  = join(__dirname, '../src/data')
mkdirSync(outDir, { recursive: true })
writeFileSync(join(outDir, 'mockData.json'), JSON.stringify({
  neighborhood: 'Downtown LA',
  center: [CENTER_LNG, CENTER_LAT],
  timeframes, hotspots, agents, interventions,
}, null, 2))

console.log(`✓ Generated mockData.json`)
console.log(`  ${cells.length} cells × ${timeframes.length} timeframes (hours 6–22)`)
console.log(`  Hotspot cells: ${hotspots.map(h => h.h3_index).join(', ')}`)
