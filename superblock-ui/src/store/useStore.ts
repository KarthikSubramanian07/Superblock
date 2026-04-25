import { create } from 'zustand'
import type { Tile, Hotspot, Agent, Intervention, SimResult, ActiveTab } from '@/types'
import { getMockTilesAtIndex, getMockHotspot, getMockNearestHotspot, getMockAgents, getMockInterventions } from '@/data/mock'
import { fetchLiveAgents, simulateIntervention, fetchPlannerInterventions } from '@/lib/api'
import { INITIAL_HOUR, SIM_MOCK_DELAY_MS } from '@/lib/config'
import type { Hotspot as HotspotType } from '@/types'


interface StoreState {
  // Connection
  isLive: boolean
  isConnecting: boolean
  isDemoMode: boolean
  toggleDemoMode: () => void
  setIsLive: (live: boolean) => void
  setIsConnecting: (v: boolean) => void

  // Time (hour: 6–22)
  timeIndex: number
  setTimeIndex: (hour: number) => void

  // Map
  tiles: Tile[]
  setTiles: (tiles: Tile[]) => void
  liveHotspots: HotspotType[]
  setLiveHotspots: (hotspots: HotspotType[]) => void
  selectedHexId: string | null
  setSelectedHex: (id: string | null) => void

  // Panels
  activeTab: ActiveTab
  setActiveTab: (tab: ActiveTab) => void

  // Agents
  agents: Agent[]
  setAgents: (agents: Agent[]) => void
  fetchLiveAgents: () => Promise<void>

  // Hotspot
  selectedHotspot: Hotspot | null

  // Simulation
  simRunning: boolean
  simResult: SimResult | null
  selectedInterventionId: string | null
  setSelectedIntervention: (id: string) => void
  runSimulation: () => Promise<void>

  // Interventions
  interventions: Intervention[]
  rankedInterventions: Intervention[]
  liveRankedInterventions: Intervention[] | null
  setLiveRankedInterventions: (items: Intervention[] | null) => void
}

export const useStore = create<StoreState>()((set, get) => ({
  // Connection
  isLive: false,
  isConnecting: false,
  isDemoMode: true,
  toggleDemoMode: () => set(s => ({ isDemoMode: !s.isDemoMode })),
  setIsLive: async (live: boolean) => {
    set({ isLive: live })
    if (live) {
      const [liveAgents, livePlanner] = await Promise.all([
        fetchLiveAgents(),
        fetchPlannerInterventions(),
      ])
      if (liveAgents) set({ agents: liveAgents })
      if (livePlanner) set({ liveRankedInterventions: livePlanner })
    } else {
      set({ agents: getMockAgents(), liveRankedInterventions: null })
    }
  },
  setIsConnecting: (v: boolean) => set({ isConnecting: v }),

  // Time
  timeIndex: INITIAL_HOUR,
  setTimeIndex: (hour: number) => set({ timeIndex: hour, tiles: getMockTilesAtIndex(hour) }),

  // Map
  tiles: getMockTilesAtIndex(INITIAL_HOUR),
  setTiles: (tiles: Tile[]) => set({ tiles }),
  liveHotspots: [],
  setLiveHotspots: (hotspots: HotspotType[]) => set({ liveHotspots: hotspots }),
  selectedHexId: null,
  setSelectedHex: (id: string | null) => {
    if (!id) {
      set({ selectedHexId: null, selectedHotspot: null })
      return
    }
    // Live hotspots take priority; fall back to mock exact match; then synthesise from nearest
    let hotspot = get().liveHotspots.find(h => h.h3_index === id) ?? getMockHotspot(id)
    if (!hotspot) {
      const tile = get().tiles.find(t => t.h3_index === id)
      if (tile) {
        const nearest = getMockNearestHotspot(id)
        if (nearest) {
          hotspot = {
            ...nearest,
            h3_index: id,
            als_score: tile.als_score,
            noise_db: tile.noise_db,
            context: tile.context,
          }
        }
      }
    }
    set({ selectedHexId: id, selectedHotspot: hotspot, activeTab: 'hotspot' })
  },

  // Panels
  activeTab: 'agents',
  setActiveTab: (tab: ActiveTab) => set({ activeTab: tab }),

  // Agents
  agents: getMockAgents(),
  setAgents: (agents: Agent[]) => set({ agents }),
  fetchLiveAgents: async () => {
    const liveAgents = await fetchLiveAgents()
    if (liveAgents) {
      set({ agents: liveAgents })
    }
  },

  // Hotspot
  selectedHotspot: null,

  // Simulation
  simRunning: false,
  simResult: null,
  selectedInterventionId: null,
  setSelectedIntervention: (id: string) => set({ selectedInterventionId: id || null, simResult: null }),
  runSimulation: async () => {
    const { selectedHotspot, selectedInterventionId, interventions } = get()
    const intervention = interventions.find(i => i.id === selectedInterventionId)
    if (!intervention || !selectedHotspot) return

    const alsBefore = selectedHotspot.als_score
    set({ simRunning: true, simResult: null })

    try {
      const result = await simulateIntervention({
        h3_index: selectedHotspot.h3_index,
        intervention_id: intervention.id,
        als_before: alsBefore,
      })

      if (result) {
        set({ simRunning: false, simResult: result })
        return
      }
    } catch {
      // fall back to client-side mock simulation if backend is unavailable
    }

    const alsAfter = Math.max(0.01, alsBefore + intervention.predicted_als_delta)
    const alsDelta = Math.round((alsAfter - alsBefore) * 100) / 100
    const percentReduction = Math.round((Math.abs(alsDelta) / alsBefore) * 100)

    await new Promise(resolve => setTimeout(resolve, SIM_MOCK_DELAY_MS))
    set({
      simRunning: false,
      simResult: {
        intervention_id: intervention.id,
        h3_index: selectedHotspot.h3_index,
        als_before: Math.round(alsBefore * 100) / 100,
        als_after: Math.round(alsAfter * 100) / 100,
        als_delta: alsDelta,
        percent_reduction: percentReduction,
      },
    })
  },

  // Interventions
  interventions: getMockInterventions(),
  rankedInterventions: [...getMockInterventions()].sort(
    (a, b) => b.relief_coefficient - a.relief_coefficient
  ),
  liveRankedInterventions: null,
  setLiveRankedInterventions: (items) => set({ liveRankedInterventions: items }),
}))
