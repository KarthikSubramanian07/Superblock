import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, Cell, LabelList,
} from 'recharts'
import { useStore } from '@/store/useStore'
import type { Intervention } from '@/types'

const CHART_COLORS = ['#6366f1', '#818cf8', '#a5b4fc', '#c7d2fe']

function InterventionChart() {
  const rankedInterventions     = useStore(s => s.rankedInterventions)
  const liveRankedInterventions = useStore(s => s.liveRankedInterventions)
  const isLive                  = useStore(s => s.isLive)
  const interventions           = (isLive && liveRankedInterventions) ? liveRankedInterventions : rankedInterventions

  const data = interventions.map(item => ({
    name: item.icon + ' ' + item.label,
    impact: Math.abs(Math.round(item.predicted_als_delta * 100)),
    cost: item.estimated_cost_usd >= 1000
      ? `$${(item.estimated_cost_usd / 1000).toFixed(0)}k`
      : `$${item.estimated_cost_usd}`,
  }))

  return (
    <div style={{
      background: '#ffffff', border: '1px solid #e2e8f0',
      borderRadius: '10px', padding: '14px 16px', marginTop: '4px',
    }}>
      <p style={{ fontSize: '0.72rem', fontWeight: 600, color: '#334155', marginBottom: '4px' }}>
        Cost vs. Impact
      </p>
      <p style={{ fontSize: '0.65rem', color: '#94a3b8', marginBottom: '12px' }}>
        Ranked by relief per dollar (best → worst)
      </p>
      <ResponsiveContainer width="100%" height={150}>
        <BarChart data={data} layout="vertical" margin={{ top: 0, right: 40, left: 4, bottom: 0 }}>
          <XAxis type="number" domain={[0, 35]} unit="%" tick={{ fontSize: 9, fill: '#94a3b8' }} />
          <YAxis
            type="category" dataKey="name" width={110}
            tick={{ fontSize: 9, fill: '#475569' }}
          />
          <Tooltip
            formatter={(val, _name, props) => [`${val}% ALS reduction · cost ${props.payload.cost}`, 'Impact']}
            contentStyle={{ fontSize: '0.72rem', borderRadius: '7px', border: '1px solid #e2e8f0' }}
          />
          <Bar dataKey="impact" radius={[0, 4, 4, 0]} barSize={18}>
            {data.map((_d, i) => <Cell key={i} fill={CHART_COLORS[i]} />)}
            <LabelList dataKey="cost" position="right" style={{ fontSize: '9px', fill: '#94a3b8' }} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

function formatCost(usd: number): string {
  if (usd >= 1000) return `$${(usd / 1000).toFixed(0)}k`
  return `$${usd}`
}

function InterventionCard({
  item,
  selected,
  onSelect,
}: {
  item: Intervention
  selected: boolean
  onSelect: () => void
}) {
  const delta = item.predicted_als_delta
  const deltaLabel = `${delta > 0 ? '+' : ''}${Math.round(delta * 100)}%`

  return (
    <button
      onClick={onSelect}
      style={{
        width: '100%', textAlign: 'left', padding: '11px 13px',
        borderRadius: '9px', cursor: 'pointer',
        background: selected ? '#eef2ff' : '#ffffff',
        border: `1.5px solid ${selected ? '#6366f1' : '#e2e8f0'}`,
        transition: 'border-color 0.15s, background 0.15s',
      }}
    >
      <div className="flex items-center gap-2" style={{ marginBottom: '4px' }}>
        <span style={{ fontSize: '1.1rem' }}>{item.icon}</span>
        <span style={{ fontSize: '0.82rem', fontWeight: 600, color: '#0f172a', flex: 1 }}>{item.label}</span>
        <span style={{
          fontSize: '0.7rem', fontWeight: 700,
          color: '#16a34a', background: '#f0fdf4',
          border: '1px solid #bbf7d0', borderRadius: '99px', padding: '1px 7px',
        }}>
          {deltaLabel} ALS
        </span>
      </div>
      <p style={{ fontSize: '0.7rem', color: '#64748b', marginBottom: '5px' }}>{item.description}</p>
      <span style={{ fontSize: '0.68rem', color: '#94a3b8' }}>Est. cost: {formatCost(item.estimated_cost_usd)}</span>
    </button>
  )
}

export default function SimPanel() {
  const selectedHotspot         = useStore(s => s.selectedHotspot)
  const rankedInterventionsBase = useStore(s => s.rankedInterventions)
  const liveRankedInterventions = useStore(s => s.liveRankedInterventions)
  const isLive                  = useStore(s => s.isLive)
  const rankedInterventions     = (isLive && liveRankedInterventions) ? liveRankedInterventions : rankedInterventionsBase
  const selectedInterventionId = useStore(s => s.selectedInterventionId)
  const setSelectedIntervention = useStore(s => s.setSelectedIntervention)
  const runSimulation          = useStore(s => s.runSimulation)
  const simRunning             = useStore(s => s.simRunning)
  const simResult              = useStore(s => s.simResult)
  const setActiveTab           = useStore(s => s.setActiveTab)

  if (!selectedHotspot) {
    return (
      <div className="p-4 flex flex-col gap-3">
        <div className="flex flex-col items-center justify-center text-center" style={{ padding: '24px 0 16px' }}>
          <div style={{ fontSize: '2.5rem', marginBottom: '12px' }}>⚡</div>
          <p style={{ color: '#64748b', fontSize: '0.875rem' }}>Select a hotspot first</p>
          <p style={{ color: '#94a3b8', fontSize: '0.75rem', marginTop: '4px' }}>Click a red zone on the map, then return here</p>
          <button
            onClick={() => setActiveTab('hotspot')}
            style={{
              marginTop: '16px', padding: '7px 18px', borderRadius: '7px',
              background: '#f1f5f9', border: '1px solid #e2e8f0',
              fontSize: '0.75rem', color: '#475569', cursor: 'pointer',
            }}
          >
            Go to Hotspot tab →
          </button>
        </div>
        <InterventionChart />
      </div>
    )
  }

  const alsBefore = selectedHotspot.als_score
  const beforePct = Math.round(alsBefore * 100)

  return (
    <div className="p-4 flex flex-col gap-3">
      <p style={{ color: '#94a3b8', fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
        Simulate Intervention
      </p>

      {/* Current hotspot summary */}
      <div style={{
        background: '#ffffff', border: '1px solid #e2e8f0',
        borderRadius: '10px', padding: '11px 14px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <div>
          <p style={{ fontSize: '0.75rem', fontWeight: 600, color: '#334155' }}>{selectedHotspot.location_label}</p>
          <p style={{ fontSize: '0.68rem', color: '#94a3b8' }}>Current stress zone</p>
        </div>
        <span style={{
          fontSize: '1rem', fontWeight: 800,
          color: alsBefore >= 0.7 ? '#dc2626' : alsBefore >= 0.5 ? '#ea580c' : '#ca8a04',
        }}>
          {beforePct}% ALS
        </span>
      </div>

      {/* Intervention cards */}
      <p style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: 600 }}>Choose an intervention:</p>
      <div className="flex flex-col gap-2">
        {rankedInterventions.map(item => (
          <InterventionCard
            key={item.id}
            item={item}
            selected={item.id === selectedInterventionId}
            onSelect={() => setSelectedIntervention(item.id)}
          />
        ))}
      </div>

      {/* Run button */}
      {!simResult && (
        <button
          onClick={runSimulation}
          disabled={!selectedInterventionId || simRunning}
          style={{
            width: '100%', padding: '11px', borderRadius: '8px',
            background: selectedInterventionId && !simRunning ? '#6366f1' : '#e2e8f0',
            color: selectedInterventionId && !simRunning ? 'white' : '#94a3b8',
            fontSize: '0.82rem', fontWeight: 600,
            border: 'none', cursor: selectedInterventionId && !simRunning ? 'pointer' : 'not-allowed',
            transition: 'background 0.15s',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
          }}
        >
          {simRunning ? (
            <>
              <span style={{
                width: '13px', height: '13px', borderRadius: '50%',
                border: '2px solid #94a3b8', borderTopColor: '#6366f1',
                animation: 'spin 0.7s linear infinite', display: 'inline-block',
              }} />
              Running simulation…
            </>
          ) : 'Run Simulation ⚡'}
        </button>
      )}

      {/* Result card */}
      {simResult && (
        <div style={{
          background: '#f0fdf4', border: '1.5px solid #86efac',
          borderRadius: '10px', padding: '14px 16px',
        }}>
          <p style={{ fontSize: '0.72rem', fontWeight: 700, color: '#16a34a', marginBottom: '10px' }}>
            Simulation Complete
          </p>

          {/* Before → After */}
          <div className="flex items-center justify-center gap-3" style={{ marginBottom: '12px' }}>
            <div style={{ textAlign: 'center' }}>
              <p style={{ fontSize: '0.65rem', color: '#94a3b8' }}>Before</p>
              <p style={{ fontSize: '1.4rem', fontWeight: 800, color: '#dc2626' }}>
                {Math.round(simResult.als_before * 100)}%
              </p>
            </div>
            <span style={{ fontSize: '1.2rem', color: '#94a3b8' }}>→</span>
            <div style={{ textAlign: 'center' }}>
              <p style={{ fontSize: '0.65rem', color: '#94a3b8' }}>After</p>
              <p style={{ fontSize: '1.4rem', fontWeight: 800, color: '#16a34a' }}>
                {Math.round(simResult.als_after * 100)}%
              </p>
            </div>
            <div style={{
              marginLeft: '4px', background: '#dcfce7', border: '1px solid #86efac',
              borderRadius: '99px', padding: '4px 10px', textAlign: 'center',
            }}>
              <p style={{ fontSize: '0.65rem', color: '#16a34a' }}>Reduction</p>
              <p style={{ fontSize: '0.9rem', fontWeight: 800, color: '#16a34a' }}>
                -{simResult.percent_reduction}%
              </p>
            </div>
          </div>

          <button
            onClick={() => { setSelectedIntervention(''); }}
            style={{
              width: '100%', padding: '8px', borderRadius: '7px',
              background: 'white', border: '1px solid #86efac',
              fontSize: '0.75rem', color: '#16a34a', cursor: 'pointer',
            }}
          >
            Try another intervention
          </button>
        </div>
      )}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>

      {/* Always-visible comparison chart */}
      <div style={{ borderTop: '1px solid #e2e8f0', paddingTop: '12px', marginTop: '4px' }}>
        <InterventionChart />
      </div>
    </div>
  )
}
