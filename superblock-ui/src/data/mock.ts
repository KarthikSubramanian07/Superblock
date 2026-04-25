import { gridDistance } from 'h3-js'
import type { Tile, Hotspot, Agent, Intervention } from '@/types'
import data from './mockData.json'
import { INTERVENTIONS } from './interventions.config'

export const MOCK_TIMEFRAME_COUNT = data.timeframes.length // 17 (hours 6–22)
export const MOCK_CENTER = data.center as [number, number]
export const MOCK_NEIGHBORHOOD = data.neighborhood

// hour: 6–22
export function getMockTilesAtIndex(hour: number): Tile[] {
  const index = Math.max(0, Math.min(hour - 6, MOCK_TIMEFRAME_COUNT - 1))
  return data.timeframes[index].tiles as Tile[]
}

export function getMockTimeLabel(hour: number): string {
  const index = Math.max(0, Math.min(hour - 6, MOCK_TIMEFRAME_COUNT - 1))
  return data.timeframes[index].label
}

export function getMockHotspot(h3Index: string): Hotspot | null {
  return (data.hotspots.find(h => h.h3_index === h3Index) as Hotspot) ?? null
}

// Returns the nearest named hotspot, used to enrich non-hotspot tiles
export function getMockNearestHotspot(h3Index: string): Hotspot | null {
  let nearest: (typeof data.hotspots)[0] | null = null
  let minDist = Infinity
  for (const h of data.hotspots) {
    try {
      const d = gridDistance(h3Index, h.h3_index)
      if (d < minDist) { minDist = d; nearest = h }
    } catch { /* different base cells — skip */ }
  }
  return nearest ? (nearest as Hotspot) : null
}

export function getMockAgents(): Agent[] {
  return data.agents as Agent[]
}

export function getMockInterventions(): Intervention[] {
  return INTERVENTIONS
}

export function getMockHotspotIds(): string[] {
  return data.hotspots.map(h => h.h3_index)
}
