import { useStore } from '@/store/useStore'
import { alsToLabel } from '@/lib/colorScale'

const STRESSOR_META: Record<string, { icon: string; label: string; color: string }> = {
  heat:              { icon: '🌡️', label: 'Heat Stress',       color: '#fef3c7' },
  noise:             { icon: '🔊', label: 'High Noise',        color: '#fce7f3' },
  poor_crossing:     { icon: '🚶', label: 'Poor Crossing',     color: '#ede9fe' },
  congestion:        { icon: '🚗', label: 'Congestion',        color: '#fef3c7' },
  poor_transit_flow: { icon: '🚌', label: 'Poor Transit Flow', color: '#dbeafe' },
}

const CONTEXT_META: Record<string, { icon: string; label: string }> = {
  stationary:   { icon: '🧍', label: 'Stationary' },
  walking:      { icon: '🚶', label: 'Walking' },
  transit_like: { icon: '🚌', label: 'Transit' },
}

const SEVERITY_STYLE: Record<string, { bg: string; color: string }> = {
  high:   { bg: '#fef2f2', color: '#dc2626' },
  medium: { bg: '#fff7ed', color: '#ea580c' },
  low:    { bg: '#f0fdf4', color: '#16a34a' },
}

function AlsBar({ score }: { score: number }) {
  const pct = Math.round(score * 100)
  const color = score < 0.3 ? '#78d28c' : score < 0.5 ? '#ffd03c' : score < 0.7 ? '#ff9137' : '#e14b4b'
  return (
    <div>
      <div className="flex justify-between" style={{ marginBottom: '5px' }}>
        <span style={{ fontSize: '0.7rem', color: '#64748b' }}>ALS Score</span>
        <span style={{ fontSize: '0.7rem', fontWeight: 700, color }}>{pct}%</span>
      </div>
      <div style={{ height: '7px', background: '#f1f5f9', borderRadius: '99px', overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: '99px', transition: 'width 0.4s ease' }} />
      </div>
    </div>
  )
}

export default function HotspotPanel() {
  const selectedHexId  = useStore(s => s.selectedHexId)
  const selectedHotspot = useStore(s => s.selectedHotspot)
  const tiles          = useStore(s => s.tiles)
  const setActiveTab   = useStore(s => s.setActiveTab)

  // Empty state
  if (!selectedHexId) {
    return (
      <div className="flex flex-col items-center justify-center text-center" style={{ minHeight: '300px', padding: '32px 24px' }}>
        <div style={{ fontSize: '2.5rem', marginBottom: '12px' }}>📍</div>
        <p style={{ color: '#64748b', fontSize: '0.875rem' }}>Click a colored zone on the map</p>
        <p style={{ color: '#94a3b8', fontSize: '0.75rem', marginTop: '4px' }}>to inspect its hotspot details</p>
      </div>
    )
  }

  // Non-hotspot hex clicked — show basic tile data
  if (!selectedHotspot) {
    const tile = tiles.find(t => t.h3_index === selectedHexId)
    return (
      <div className="p-4 flex flex-col gap-4">
        <p style={{ color: '#94a3b8', fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
          Zone Info
        </p>
        <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '16px' }}>
          {tile ? <AlsBar score={tile.als_score} /> : null}
          <p style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '12px', textAlign: 'center' }}>
            No hotspot profile for this zone.
            <br />Try clicking a red or orange area.
          </p>
        </div>
      </div>
    )
  }

  // Full hotspot detail
  const sev = SEVERITY_STYLE[selectedHotspot.severity] ?? SEVERITY_STYLE.medium
  const ctx = CONTEXT_META[selectedHotspot.context] ?? { icon: '📍', label: selectedHotspot.context }
  const stressLevel = alsToLabel(selectedHotspot.als_score)

  return (
    <div className="p-4 flex flex-col gap-3">
      <p style={{ color: '#94a3b8', fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
        Hotspot Detail
      </p>

      {/* Location card */}
      <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '14px 16px' }}>
        <div className="flex items-start justify-between gap-2" style={{ marginBottom: '12px' }}>
          <div>
            <p style={{ fontSize: '0.95rem', fontWeight: 700, color: '#0f172a' }}>
              {selectedHotspot.location_label}
            </p>
            <p style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '2px' }}>
              {ctx.icon} {ctx.label} · {stressLevel} stress
            </p>
          </div>
          <span style={{
            fontSize: '0.65rem', fontWeight: 600, textTransform: 'capitalize',
            background: sev.bg, color: sev.color,
            border: `1px solid ${sev.color}33`,
            borderRadius: '99px', padding: '2px 9px', flexShrink: 0,
          }}>
            {selectedHotspot.severity}
          </span>
        </div>

        <AlsBar score={selectedHotspot.als_score} />

        {/* Noise */}
        <div className="flex items-center justify-between" style={{ marginTop: '12px' }}>
          <span style={{ fontSize: '0.7rem', color: '#64748b' }}>🔊 Ambient Noise</span>
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#334155' }}>
            {selectedHotspot.noise_db} dB
          </span>
        </div>
      </div>

      {/* Stressors */}
      <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '14px 16px' }}>
        <p style={{ fontSize: '0.7rem', color: '#64748b', marginBottom: '10px', fontWeight: 600 }}>
          Active Stressors
        </p>
        <div className="flex flex-wrap gap-2">
          {selectedHotspot.stressors.map(s => {
            const meta = STRESSOR_META[s] ?? { icon: '⚠️', label: s, color: '#f1f5f9' }
            return (
              <span key={s} style={{
                fontSize: '0.72rem', padding: '4px 10px', borderRadius: '99px',
                background: meta.color, color: '#334155',
                border: '1px solid #e2e8f0',
              }}>
                {meta.icon} {meta.label}
              </span>
            )
          })}
        </div>
      </div>

      {/* CTA */}
      <button
        onClick={() => setActiveTab('simulation')}
        style={{
          width: '100%', padding: '10px', borderRadius: '8px',
          background: '#6366f1', color: 'white',
          fontSize: '0.8rem', fontWeight: 600,
          border: 'none', cursor: 'pointer',
          transition: 'background 0.15s',
        }}
        onMouseEnter={e => (e.currentTarget.style.background = '#4f46e5')}
        onMouseLeave={e => (e.currentTarget.style.background = '#6366f1')}
      >
        Run Intervention Simulation →
      </button>
    </div>
  )
}
