export default function SimPanel() {
  return (
    <div
      className="flex flex-col items-center justify-center text-center"
      style={{ minHeight: '300px', padding: '32px 24px' }}
    >
      <div style={{ fontSize: '2.5rem', marginBottom: '12px' }}>⚡</div>
      <p style={{ color: '#64748b', fontSize: '0.875rem' }}>Select a hotspot first</p>
      <p style={{ color: '#94a3b8', fontSize: '0.75rem', marginTop: '4px' }}>
        then run a what-if simulation
      </p>
      <p style={{ color: '#cbd5e1', fontSize: '0.7rem', marginTop: '32px' }}>
        Wires in Module 9
      </p>
    </div>
  )
}
