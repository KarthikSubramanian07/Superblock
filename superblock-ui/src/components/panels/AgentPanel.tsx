const AGENTS = [
  'Ingestion',
  'Mapping',
  'Diagnosis',
  'Simulation',
  'Planner',
  'Narrator',
]

export default function AgentPanel() {
  return (
    <div className="p-4 flex flex-col gap-2">
      <p style={{ color: '#4b5563', fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '4px' }}>
        Agent Status
      </p>
      {AGENTS.map(agent => (
        <div
          key={agent}
          className="flex items-center gap-3 rounded-lg"
          style={{
            padding: '10px 12px',
            background: '#1a1d2e',
            border: '1px solid #2a2d3a',
          }}
        >
          <span
            style={{
              width: '7px',
              height: '7px',
              borderRadius: '50%',
              background: '#374151',
              flexShrink: 0,
            }}
          />
          <div className="flex-1 min-w-0">
            <p style={{ fontSize: '0.8rem', color: '#d1d5db' }}>{agent} Agent</p>
            <p style={{ fontSize: '0.7rem', color: '#4b5563' }}>Waiting...</p>
          </div>
        </div>
      ))}
      <p style={{ color: '#374151', fontSize: '0.7rem', textAlign: 'center', marginTop: '12px' }}>
        Live data wires in Module 7
      </p>
    </div>
  )
}
