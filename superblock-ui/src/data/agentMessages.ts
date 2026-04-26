// Rotating status messages shown under each agent in the Agent Panel.
// Add, remove, or edit strings here — changes appear immediately in the UI.
export const AGENT_MESSAGES: Record<string, string[]> = {
  ingestion: [
    'Receiving 47 packets/min',
    'Processing batch #128',
    '47 sensors online',
    'Data stream healthy',
    'Ingesting sensor burst',
  ],
  mapping: [
    '3 red zones detected',
    'Updating hex grid…',
    'Stress delta: +0.12',
    'Recalculating boundaries',
    'New hotspot detected',
  ],
  diagnosis: [
    'Waiting for hotspot query',
    'Analysing stressor overlap',
    'Scoring ALS factors',
    'Running context classifier',
  ],
  simulation: [
    'Ready',
    'Loading intervention model',
    'Scoring candidates…',
    'Simulation complete',
  ],
  planner: [
    'Ready',
    'Awaiting diagnosis',
    'Building action plan',
    'Ranking interventions',
  ],
  narrator: [
    'Ready',
    'Drafting summary…',
    'Composing brief for judges',
  ],
}
