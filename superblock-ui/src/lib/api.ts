import type { Tile, Hotspot, Agent, SimResult, Intervention, DiagnosisResult, IngestionStatus } from '@/types'

const BASE     = (import.meta.env.VITE_API_BASE_URL      as string | undefined) ?? 'http://localhost:8000'
const P_HEALTH   = (import.meta.env.VITE_API_PATH_HEALTH   as string | undefined) ?? '/health'
const P_TILES    = (import.meta.env.VITE_API_PATH_TILES    as string | undefined) ?? '/map/tiles'
const P_HOTSPOTS = (import.meta.env.VITE_API_PATH_HOTSPOTS as string | undefined) ?? '/agents/hotspots'
const P_AGENTS   = (import.meta.env.VITE_API_PATH_AGENTS   as string | undefined) ?? '/agents'
const P_SIMULATE = (import.meta.env.VITE_API_PATH_SIMULATE as string | undefined) ?? '/simulate/intervention'
const P_PLANNER_INTERVENTIONS = (import.meta.env.VITE_API_PATH_PLANNER_INTERVENTIONS as string | undefined) ?? '/planner/interventions'
const P_DIAGNOSIS = (import.meta.env.VITE_API_PATH_DIAGNOSIS as string | undefined) ?? '/agents/diagnosis/red-zone-alerts'
const P_INGESTION_STATUS = (import.meta.env.VITE_API_PATH_INGESTION_STATUS as string | undefined) ?? '/demo/status'

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

export async function fetchLiveTiles(_hour: number): Promise<Tile[] | null> {
  const data = await get<Tile[] | { tiles: Tile[] }>(`${P_TILES}`)
  if (!data) return null
  const raw = Array.isArray(data) ? data : (data as { tiles: Tile[] }).tiles ?? null
  if (!raw) return null
  // Normalise real-backend field names (avg_als → als_score, dominant_context → context)
  return (raw as unknown as Record<string, unknown>[]).map(t => ({
    h3_index:  t.h3_index  as string,
    als_score: (t.als_score ?? t.avg_als ?? 0) as number,
    context:   (t.context   ?? t.dominant_context ?? 'stationary') as Tile['context'],
    noise_db:  (t.noise_db  ?? 0) as number,
  }))
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

export async function fetchIngestionStatus(): Promise<IngestionStatus | null> {
  // Real backend returns DemoStatusResponse — map to IngestionStatus shape
  const data = await get<{ edge_packet_count: number; unique_edge_users: number; active_tile_count: number; red_zone_count: number }>(P_INGESTION_STATUS)
  if (!data) return null
  return {
    packets_per_min: data.edge_packet_count,
    sensors_online: data.unique_edge_users,
    last_batch_id: data.active_tile_count,
    total_tiles: data.active_tile_count,
    status: 'active',
  }
}

export async function fetchDiagnosis(h3_index: string): Promise<DiagnosisResult | null> {
  // Real backend returns { alerts: [...], alert_count: N } — map first alert to DiagnosisResult
  const data = await get<{ alerts: Array<{ h3_index: string; summary: string; primary_stressor: string; stressors: string[]; als_score: number; severity: string; recommended_action: string }> }>(P_DIAGNOSIS)
  if (!data?.alerts?.length) return null
  const alert = data.alerts.find(a => a.h3_index === h3_index) ?? data.alerts[0]
  return {
    h3_index: alert.h3_index,
    summary: alert.summary,
    primary_stressor: alert.primary_stressor,
    stressors: alert.stressors ?? [],
    als_score: alert.als_score,
    severity: alert.severity as DiagnosisResult['severity'],
    recommended_action: alert.recommended_action,
  }
}

export interface NarrativeReport {
  executive_summary: string
  technical_analysis: string
  recommendations: string
  next_steps: string
}

export async function runLiveOrchestration(h3_index?: string): Promise<NarrativeReport | null> {
  try {
    const res = await fetch(`${BASE}/agents/orchestrate/live`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ h3_index: h3_index ?? null }),
      signal: AbortSignal.timeout(40000),
    })
    console.log('[orchestrate/live] status:', res.status)
    if (!res.ok) {
      const text = await res.text()
      console.error('[orchestrate/live] error body:', text)
      return null
    }
    const data = await res.json()
    console.log('[orchestrate/live] narrative_report:', data.narrative_report)
    return (data.narrative_report as NarrativeReport) ?? null
  } catch (err) {
    console.error('[orchestrate/live] fetch error:', err)
    return null
  }
}

export async function fetchPlannerInterventions(): Promise<Intervention[] | null> {
  return get<Intervention[]>(P_PLANNER_INTERVENTIONS)
}

// Map frontend intervention IDs to real backend intervention_type values
const INTERVENTION_ID_MAP: Record<string, string> = {
  shade_canopy:        'shade_canopy',
  longer_walk_signal:  'longer_crossing_time',
  parklet:             'parklet',
  pedestrian_bridge:   'pedestrian_bridge',
}

export async function simulateIntervention(payload: { h3_index: string; intervention_id: string; als_before: number }): Promise<SimResult | null> {
  try {
    const intervention_type = INTERVENTION_ID_MAP[payload.intervention_id] ?? payload.intervention_id
    const res = await fetch(`${BASE}${P_SIMULATE}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ h3_index: payload.h3_index, intervention_type, intensity: 1.0, budget_usd: 0 }),
    })
    if (!res.ok) return null
    const data = await res.json()
    const alsBefore = data.before?.avg_als ?? payload.als_before
    const alsAfter  = data.after?.avg_als  ?? alsBefore
    const alsDelta  = Math.round((alsAfter - alsBefore) * 100) / 100
    const percentReduction = alsBefore > 0 ? Math.round((Math.abs(alsDelta) / alsBefore) * 100) : 0
    return {
      intervention_id:   payload.intervention_id,
      h3_index:          payload.h3_index,
      als_before:        Math.round(alsBefore * 100) / 100,
      als_after:         Math.round(alsAfter  * 100) / 100,
      als_delta:         alsDelta,
      percent_reduction: percentReduction,
    }
  } catch {
    return null
  }
}
