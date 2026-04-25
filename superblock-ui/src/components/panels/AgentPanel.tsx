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
      <p style={{ color: '#94a3b8', fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '4px' }}>
        Agent Status
      </p>
      {AGENTS.map(agent => (
        <div
          key={agent}
          className="flex items-center gap-3 rounded-lg"
          style={{
            padding: '10px 12px',
            background: '#ffffff',
            border: '1px solid #e2e8f0',
          }}
        >
          <span
            style={{
              width: '7px',
              height: '7px',
              borderRadius: '50%',
              background: '#cbd5e1',
              flexShrink: 0,
            }}
          />
          <div className="flex-1 min-w-0">
            <p style={{ fontSize: '0.8rem', color: '#334155' }}>{agent} Agent</p>
            <p style={{ fontSize: '0.7rem', color: '#94a3b8' }}>Waiting...</p>
          </div>
        </div>
      ))}
      <p style={{ color: '#cbd5e1', fontSize: '0.7rem', textAlign: 'center', marginTop: '12px' }}>
        Live data wires in Module 7
      </p>
    </div>
  )
}
