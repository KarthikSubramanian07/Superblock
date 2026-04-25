import type { Intervention } from '@/types'

// All intervention options shown in the Simulation Panel.
// Edit label, icon, cost, ALS delta, or description here — no script re-run needed.
// predicted_als_delta: negative = stress reduction (e.g. -0.24 = drops ALS by 24 points)
// relief_coefficient:  impact per dollar — higher = better bang for buck (used for ranking)
export const INTERVENTIONS: Intervention[] = [
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
