import type { Tile, Hotspot, Agent, Intervention } from '@/types'
import data from './mockData.json'

export const MOCK_TIMEFRAME_COUNT = data.timeframes.length // 17 (hours 6–22)
export const MOCK_CENTER = data.center as [number, number]
export const MOCK_NEIGHBORHOOD = data.neighborhood

export function getMockTilesAtIndex(timeIndex: number): Tile[] {
  const frame = data.timeframes[Math.max(0, Math.min(timeIndex, MOCK_TIMEFRAME_COUNT - 1))]
  return frame.tiles as Tile[]
}

export function getMockTimeLabel(timeIndex: number): string {
  const frame = data.timeframes[Math.max(0, Math.min(timeIndex, MOCK_TIMEFRAME_COUNT - 1))]
  return frame.label
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
