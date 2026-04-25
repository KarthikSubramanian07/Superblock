import { create } from 'zustand'
import type { Tile, Hotspot, Agent, Intervention, SimResult, ActiveTab } from '@/types'
import { getMockTilesAtIndex, getMockHotspot, getMockAgents, getMockInterventions } from '@/data/mock'
import { SIM_MOCK_DELAY_MS } from '@/lib/constants'

const INITIAL_HOUR = 14 // 2 PM — peak stress, good for judge demo

interface StoreState {
  // Connection
  isLive: boolean
  isDemoMode: boolean
  toggleDemoMode: () => void

  // Time (hour: 6–22)
  timeIndex: number
  setTimeIndex: (hour: number) => void

  // Map
  tiles: Tile[]
  selectedHexId: string | null
  setSelectedHex: (id: string | null) => void

  // Panels
  activeTab: ActiveTab
  setActiveTab: (tab: ActiveTab) => void

  // Agents
  agents: Agent[]

  // Hotspot
  selectedHotspot: Hotspot | null

  // Simulation
  simRunning: boolean
  simResult: SimResult | null
  selectedInterventionId: string | null
  setSelectedIntervention: (id: string) => void
  runSimulation: () => void

  // Interventions
  interventions: Intervention[]
  rankedInterventions: Intervention[]
}

export const useStore = create<StoreState>()((set, get) => ({
  // Connection
  isLive: false,
  isDemoMode: true,
  toggleDemoMode: () => set(s => ({ isDemoMode: !s.isDemoMode })),

  // Time
  timeIndex: INITIAL_HOUR,
  setTimeIndex: (hour: number) => set({ timeIndex: hour, tiles: getMockTilesAtIndex(hour) }),

  // Map
  tiles: getMockTilesAtIndex(INITIAL_HOUR),
  selectedHexId: null,
  setSelectedHex: (id: string | null) => {
    if (!id) {
      set({ selectedHexId: null, selectedHotspot: null })
      return
    }
    set({
      selectedHexId: id,
      selectedHotspot: getMockHotspot(id),
      activeTab: 'hotspot',
    })
  },

  // Panels
  activeTab: 'agents',
  setActiveTab: (tab: ActiveTab) => set({ activeTab: tab }),

  // Agents
  agents: getMockAgents(),

  // Hotspot
  selectedHotspot: null,

  // Simulation
  simRunning: false,
  simResult: null,
  selectedInterventionId: null,
  setSelectedIntervention: (id: string) => set({ selectedInterventionId: id, simResult: null }),
  runSimulation: () => {
    const { selectedHotspot, selectedInterventionId, interventions } = get()
    const intervention = interventions.find(i => i.id === selectedInterventionId)
    if (!intervention) return

    const alsBefore = selectedHotspot?.als_score ?? 0.75
    const alsAfter = Math.max(0.01, alsBefore + intervention.predicted_als_delta)
    const alsDelta = Math.round((alsAfter - alsBefore) * 100) / 100
    const percentReduction = Math.round((Math.abs(alsDelta) / alsBefore) * 100)

    set({ simRunning: true })

    setTimeout(() => {
      set({
        simRunning: false,
        simResult: {
          intervention_id: intervention.id,
          h3_index: selectedHotspot?.h3_index ?? '',
          als_before: Math.round(alsBefore * 100) / 100,
          als_after: Math.round(alsAfter * 100) / 100,
          als_delta: alsDelta,
          percent_reduction: percentReduction,
        },
      })
    }, SIM_MOCK_DELAY_MS)
  },

  // Interventions
  interventions: getMockInterventions(),
  rankedInterventions: [...getMockInterventions()].sort(
    (a, b) => b.relief_coefficient - a.relief_coefficient
  ),
}))
