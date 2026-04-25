import type { Tile, Hotspot, Agent, Intervention } from '@/types'
import data from './mockData.json'

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
  const found = data.hotspots.find(h => h.h3_index === h3Index)
  return (found as Hotspot) ?? null
}

export function getMockAgents(): Agent[] {
  return data.agents as Agent[]
}

export function getMockInterventions(): Intervention[] {
  return data.interventions as Intervention[]
}

export function getMockHotspotIds(): string[] {
  return data.hotspots.map(h => h.h3_index)
}
