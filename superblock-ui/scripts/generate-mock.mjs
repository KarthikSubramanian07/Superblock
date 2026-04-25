// Generates src/data/mockData.json using real H3 indices for DTLA
import { latLngToCell, gridDisk } from 'h3-js'
import { writeFileSync, mkdirSync } from 'fs'
import { fileURLToPath } from 'url'
import { dirname, join } from 'path'

const __dirname = dirname(fileURLToPath(import.meta.url))

const CENTER_LAT = 34.0522
const CENTER_LNG = -118.2437
const H3_RES = 9

const centerCell = latLngToCell(CENTER_LAT, CENTER_LNG, H3_RES)
const cells = gridDisk(centerCell, 2) // ~19 cells covering a neighborhood

const HOTSPOT_INDICES = [0, 4, 9]
const CONTEXTS = ['stationary', 'walking', 'transit_like']

const HOURLY_STRESS = {
  6: 0.15, 7: 0.25, 8: 0.45, 9: 0.55,
  10: 0.50, 11: 0.60, 12: 0.65, 13: 0.70,
  14: 0.85, 15: 0.80, 16: 0.75, 17: 0.70,
  18: 0.65, 19: 0.55, 20: 0.45, 21: 0.35, 22: 0.25
}

function seeded(seed) {
  const x = Math.sin(seed + 1) * 10000
  return x - Math.floor(x)
}

function clamp(v, lo, hi) {
  return Math.max(lo, Math.min(hi, v))
}

// --- Timeframes ---
const timeframes = []
for (let hour = 6; hour <= 22; hour++) {
  const factor = HOURLY_STRESS[hour]
  const label = hour < 12 ? `${hour}:00 AM` : hour === 12 ? '12:00 PM' : `${hour - 12}:00 PM`

  const tiles = cells.map((cell, i) => {
    const isHot = HOTSPOT_INDICES.includes(i)
    const seed = i * 100 + hour

    const base = isHot
      ? 0.55 + factor * 0.38
      : 0.05 + factor * 0.50
    const als = clamp(base + (seeded(seed) - 0.5) * 0.10, 0.05, 0.98)

    const noiseBase = isHot ? 72 : 50
    const noise_db = clamp(noiseBase + seeded(seed + 300) * 18 + factor * 14, 40, 95)

    return {
      h3_index: cell,
      als_score: Math.round(als * 100) / 100,
      context: CONTEXTS[Math.floor(seeded(seed + 200) * 3)],
      noise_db: Math.round(noise_db * 10) / 10,
    }
  })

  timeframes.push({ label, time_index: hour - 6, hour, tiles })
}

// --- Hotspots ---
const hotspots = [
  {
    h3_index: cells[HOTSPOT_INDICES[0]],
    stressors: ['heat', 'noise'],
    severity: 'high',
    als_score: 0.84,
    noise_db: 82.0,
    context: 'stationary',
    location_label: '5th & Grand Ave',
  },
  {
    h3_index: cells[HOTSPOT_INDICES[1]],
    stressors: ['poor_crossing', 'congestion'],
    severity: 'high',
    als_score: 0.79,
    noise_db: 76.5,
    context: 'stationary',
    location_label: 'Figueroa & 7th St',
  },
  {
    h3_index: cells[HOTSPOT_INDICES[2]],
    stressors: ['heat', 'poor_transit_flow'],
    severity: 'medium',
    als_score: 0.68,
    noise_db: 69.0,
    context: 'walking',
    location_label: 'Hope St Corridor',
  },
]

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
  {
    id: 'shade_canopy',
    label: 'Shade Canopy',
    icon: '🌿',
    predicted_als_delta: -0.24,
    estimated_cost_usd: 8500,
    relief_coefficient: 0.0000282,
    description: 'Install shade sails along 5th St reducing surface temp by 4°C',
  },
  {
    id: 'longer_walk_signal',
    label: 'Longer Walk Signal',
    icon: '🚦',
    predicted_als_delta: -0.14,
    estimated_cost_usd: 1200,
    relief_coefficient: 0.0001167,
    description: 'Extend pedestrian crossing time by 15s at 5th & Grand',
  },
  {
    id: 'parklet',
    label: 'Parklet',
    icon: '🪑',
    predicted_als_delta: -0.18,
    estimated_cost_usd: 12000,
    relief_coefficient: 0.000015,
    description: 'Install resting parklet with seating and greenery',
  },
  {
    id: 'pedestrian_bridge',
    label: 'Pedestrian Bridge',
    icon: '🌉',
    predicted_als_delta: -0.31,
    estimated_cost_usd: 95000,
    relief_coefficient: 0.00000326,
    description: 'Grade-separated crossing eliminating vehicle conflict zone',
  },
]

// --- Write output ---
const outDir = join(__dirname, '../src/data')
mkdirSync(outDir, { recursive: true })

const outPath = join(outDir, 'mockData.json')
writeFileSync(outPath, JSON.stringify({
  neighborhood: 'Downtown LA',
  center: [CENTER_LNG, CENTER_LAT],
  timeframes,
  hotspots,
  agents,
  interventions,
}, null, 2))

console.log(`✓ Generated mockData.json`)
console.log(`  ${cells.length} cells × ${timeframes.length} timeframes (hours 6–22)`)
console.log(`  Hotspot cells: ${hotspots.map(h => h.h3_index).join(', ')}`)
