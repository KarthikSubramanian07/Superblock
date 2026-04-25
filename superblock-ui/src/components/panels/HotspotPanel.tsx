export default function HotspotPanel() {
  return (
    <div
      className="flex flex-col items-center justify-center text-center"
      style={{ minHeight: '300px', padding: '32px 24px' }}
    >
      <div style={{ fontSize: '2.5rem', marginBottom: '12px' }}>📍</div>
      <p style={{ color: '#9ca3af', fontSize: '0.875rem' }}>Click a red zone on the map</p>
      <p style={{ color: '#4b5563', fontSize: '0.75rem', marginTop: '4px' }}>
        to inspect its hotspot details
      </p>
      <p style={{ color: '#374151', fontSize: '0.7rem', marginTop: '32px' }}>
        Wires in Module 8
      </p>
    </div>
  )
}
