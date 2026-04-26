// Edit the help text here — shown on hover next to each agent in the Agent Panel
export const AGENT_HELP: Record<string, string> = {
  ingestion:
    'Receives raw ALS sensor packets from Apple Watch devices in the field. Validates, deduplicates, and forwards clean data to the Mapping Agent.',
  mapping:
    'Assigns each sensor reading to an H3 hexagonal grid cell and computes the ALS stress score per zone. Detects red-zone threshold crossings.',
  diagnosis:
    'Analyses active hotspots to identify root stressors — heat, noise, poor crossings, or congestion — using context and historical patterns.',
  simulation:
    'Runs what-if models for proposed interventions against the current stress field. Returns predicted ALS delta and relief estimates.',
  planner:
    'Ranks intervention options by biological relief coefficient (impact per dollar) and builds an actionable recommendation list.',
  narrator:
    'Synthesises findings from all agents into a plain-language summary for city planners and first responders.',
}
