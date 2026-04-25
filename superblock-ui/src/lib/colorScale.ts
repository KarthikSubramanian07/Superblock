// Semi-transparent flat zone colors — streets and labels show through.
// Progressive alpha: outer low-stress edges fade more, centers stay vivid.
export function alsToColor(score: number): [number, number, number, number] {
  if (score < 0.3) return [120, 210, 140, 100]  // soft green — very transparent at edges
  if (score < 0.5) return [255, 208,  60, 120]  // soft yellow
  if (score < 0.7) return [255, 145,  55, 140]  // soft orange
  return               [225,  75,  75, 155]  // soft red — most opaque at hotspots
}

export function alsToLabel(score: number): string {
  if (score < 0.3) return 'Low'
  if (score < 0.5) return 'Moderate'
  if (score < 0.7) return 'High'
  return 'Critical'
}
