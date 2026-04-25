export interface Tile {
  h3_index: string
  als_score: number
  context: 'stationary' | 'walking' | 'transit_like'
  noise_db: number
}

export interface Hotspot {
  h3_index: string
  stressors: string[]
  severity: 'low' | 'medium' | 'high'
  als_score: number
  noise_db: number
  context: string
  location_label: string
}

export interface Agent {
  id: string
  label: string
  status: 'active' | 'processing' | 'idle' | 'error'
  message: string
  timestamp?: string
}

export interface Intervention {
  id: string
  label: string
  icon: string
  predicted_als_delta: number
  estimated_cost_usd: number
  relief_coefficient: number
  description: string
}

export interface SimResult {
  intervention_id: string
  h3_index: string
  als_before: number
  als_after: number
  als_delta: number
  percent_reduction: number
}

export type ActiveTab = 'agents' | 'hotspot' | 'simulation'
