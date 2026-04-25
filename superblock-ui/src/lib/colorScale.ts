export function alsToColor(score: number): [number, number, number, number] {
  if (score < 0.3) return [34, 197, 94, 200]   // green
  if (score < 0.5) return [234, 179, 8, 200]    // yellow
  if (score < 0.7) return [249, 115, 22, 200]   // orange
  return [239, 68, 68, 220]                      // red
}

export function alsToLabel(score: number): string {
  if (score < 0.3) return 'Low'
  if (score < 0.5) return 'Moderate'
  if (score < 0.7) return 'High'
  return 'Critical'
}
