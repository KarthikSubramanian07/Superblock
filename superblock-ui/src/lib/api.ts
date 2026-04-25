import type { Tile, Hotspot, Agent, SimResult, Intervention } from '@/types'

const BASE     = (import.meta.env.VITE_API_BASE_URL      as string | undefined) ?? 'http://localhost:8000'
const P_HEALTH   = (import.meta.env.VITE_API_PATH_HEALTH   as string | undefined) ?? '/health'
const P_TILES    = (import.meta.env.VITE_API_PATH_TILES    as string | undefined) ?? '/tiles'
const P_HOTSPOTS = (import.meta.env.VITE_API_PATH_HOTSPOTS as string | undefined) ?? '/hotspots'
const P_AGENTS   = (import.meta.env.VITE_API_PATH_AGENTS   as string | undefined) ?? '/agents'
const P_SIMULATE = (import.meta.env.VITE_API_PATH_SIMULATE as string | undefined) ?? '/simulate'
const P_PLANNER_INTERVENTIONS = (import.meta.env.VITE_API_PATH_PLANNER_INTERVENTIONS as string | undefined) ?? '/planner/interventions'

async function get<T>(path: string, timeoutMs = 3000): Promise<T | null> {
  try {
    const res = await fetch(`${BASE}${path}`, { signal: AbortSignal.timeout(timeoutMs) })
    if (!res.ok) return null
    return (await res.json()) as T
  } catch {
    return null
  }
}

export async function checkHealth(): Promise<boolean> {
  const timeout = Number(import.meta.env.VITE_HEALTH_TIMEOUT_MS ?? 2000)
  try {
    const res = await fetch(`${BASE}${P_HEALTH}`, { signal: AbortSignal.timeout(timeout) })
    return res.ok
  } catch {
    return false
  }
}

export async function fetchLiveTiles(hour: number): Promise<Tile[] | null> {
  const data = await get<Tile[] | { tiles: Tile[] }>(`${P_TILES}?hour=${hour}`)
  if (!data) return null
  return Array.isArray(data) ? data : (data as { tiles: Tile[] }).tiles ?? null
}

export async function fetchLiveHotspots(): Promise<Hotspot[] | null> {
  const data = await get<Hotspot[] | { hotspots: Hotspot[] }>(P_HOTSPOTS)
  if (!data) return null
  return Array.isArray(data) ? data : (data as { hotspots: Hotspot[] }).hotspots ?? null
}

export async function fetchLiveAgents(): Promise<Agent[] | null> {
  const data = await get<Agent[] | { agents: Agent[] }>(P_AGENTS)
  if (!data) return null
  return Array.isArray(data) ? data : (data as { agents: Agent[] }).agents ?? null
}

export async function fetchPlannerInterventions(): Promise<Intervention[] | null> {
  return get<Intervention[]>(P_PLANNER_INTERVENTIONS)
}

export async function simulateIntervention(payload: { h3_index: string; intervention_id: string; als_before: number }): Promise<SimResult | null> {
  try {
    const res = await fetch(`${BASE}${P_SIMULATE}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (!res.ok) return null
    return (await res.json()) as SimResult
  } catch {
    return null
  }
}
