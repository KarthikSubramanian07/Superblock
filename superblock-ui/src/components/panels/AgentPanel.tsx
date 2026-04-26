import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { useStore } from '@/store/useStore'
import { AGENT_HELP } from '@/data/agentHelp'
import { AGENT_MESSAGES } from '@/data/agentMessages'
import { runLiveOrchestration } from '@/lib/api'
import type { NarrativeReport } from '@/lib/api'
import type { Agent } from '@/types'

// Rotating messages per agent to simulate live activity
function HelpIcon({ text }: { text?: string }) {
  const [coords, setCoords] = useState<{ top: number; left: number } | null>(null)
  const ref = useRef<HTMLSpanElement>(null)

  if (!text) return null

  function handleMouseEnter() {
    if (!ref.current) return
    const r = ref.current.getBoundingClientRect()
    setCoords({ top: r.bottom + 6, left: r.left + r.width / 2 })
  }

  return (
    <span
      ref={ref}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={() => setCoords(null)}
      style={{ display: 'inline-flex', flexShrink: 0, cursor: 'default' }}
    >
      {/* ? circle */}
      <span style={{
        width: '14px', height: '14px', borderRadius: '50%',
        background: '#e2e8f0', color: '#64748b',
        fontSize: '0.6rem', fontWeight: 700,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        userSelect: 'none',
      }}>
        ?
      </span>

      {/* Portal tooltip — renders into document.body, never clipped by overflow */}
      {coords && createPortal(
        <span style={{
          position: 'fixed',
          top: coords.top,
          left: coords.left,
          transform: 'translateX(-50%)',
          background: '#1e293b', color: '#f1f5f9',
          fontSize: '0.68rem', lineHeight: '1.5',
          padding: '8px 11px', borderRadius: '7px',
          width: '230px', zIndex: 9999,
          boxShadow: '0 4px 16px rgba(0,0,0,0.25)',
          pointerEvents: 'none',
          whiteSpace: 'normal',
        }}>
          {text}
          <span style={{
            position: 'absolute', bottom: '100%', left: '50%',
            transform: 'translateX(-50%)',
            width: 0, height: 0,
            borderLeft: '5px solid transparent',
            borderRight: '5px solid transparent',
            borderBottom: '5px solid #1e293b',
          }} />
        </span>,
        document.body
      )}
    </span>
  )
}


const STATUS_COLOR: Record<Agent['status'], string> = {
  active:     '#22c55e',
  processing: '#f59e0b',
  idle:       '#cbd5e1',
  error:      '#ef4444',
}

const STATUS_LABEL: Record<Agent['status'], string> = {
  active:     'Active',
  processing: 'Processing',
  idle:       'Idle',
  error:      'Error',
}

function StatusDot({ status }: { status: Agent['status'] }) {
  const color = STATUS_COLOR[status]
  const pulse = status === 'active' || status === 'processing'
  return (
    <span style={{ position: 'relative', width: '9px', height: '9px', flexShrink: 0, display: 'inline-flex' }}>
      {pulse && (
        <span style={{
          position: 'absolute', inset: 0, borderRadius: '50%',
          background: color, opacity: 0.4,
          animation: 'ping 1.4s cubic-bezier(0,0,0.2,1) infinite',
        }} />
      )}
      <span style={{ width: '9px', height: '9px', borderRadius: '50%', background: color, position: 'relative' }} />
    </span>
  )
}

export default function AgentPanel() {
  const agents = useStore(s => s.agents)
  const simRunning = useStore(s => s.simRunning)
  const selectedHotspot = useStore(s => s.selectedHotspot)
  const diagnosisResult = useStore(s => s.diagnosisResult)
  const ingestionStatus = useStore(s => s.ingestionStatus)
  const isLive = useStore(s => s.isLive)
  const selectedHexId = useStore(s => s.selectedHexId)

  const [reportLoading, setReportLoading] = useState(false)
  const [report, setReport] = useState<NarrativeReport | null>(null)
  const [reportError, setReportError] = useState<string | null>(null)

  async function handleGenerateReport() {
    setReportLoading(true)
    setReport(null)
    setReportError(null)
    const result = await runLiveOrchestration(selectedHexId ?? undefined)
    setReportLoading(false)
    if (result) {
      setReport(result)
      setDisplay(prev => ({ ...prev, narrator: { message: 'Report generated', status: 'active' } }))
    } else {
      setReportError('Report generation failed — no hotspot data or request timed out.')
    }
  }

  // Local display state — cycles messages for active agents every 3.5s
  const [display, setDisplay] = useState<Record<string, { message: string; status: Agent['status'] }>>(() =>
    Object.fromEntries(agents.map(a => [a.id, { message: a.message, status: a.status }]))
  )

  // Derive live statuses from store events
  useEffect(() => {
    setDisplay(prev => {
      const next = { ...prev }
      // Simulation agent tracks simRunning
      if (simRunning) {
        next['simulation'] = { message: 'Running simulation…', status: 'processing' }
      } else if (prev['simulation']?.status === 'processing') {
        next['simulation'] = { message: 'Simulation complete', status: 'active' }
      }
      // Ingestion agent: live mode shows real stats
      if (isLive && ingestionStatus) {
        next['ingestion'] = {
          message: `${ingestionStatus.packets_per_min} packets ingested · ${ingestionStatus.sensors_online} sensors online`,
          status: ingestionStatus.status,
        }
      }
      // Diagnosis agent: live mode shows real result; demo shows fake processing
      if (isLive && diagnosisResult) {
        next['diagnosis'] = { message: diagnosisResult.summary, status: 'active' }
      } else if (selectedHotspot) {
        next['diagnosis'] = { message: `Diagnosing ${selectedHotspot.location_label ?? 'zone'}…`, status: 'processing' }
      }
      return next
    })
  }, [simRunning, selectedHotspot, diagnosisResult, ingestionStatus, isLive])

  // Cycle messages for active/processing agents
  useEffect(() => {
    const timer = setInterval(() => {
      setDisplay(prev => {
        const next = { ...prev }
        agents.forEach(agent => {
          const current = next[agent.id]
          if (current?.status === 'active' || current?.status === 'processing') {
            const pool = AGENT_MESSAGES[agent.id]
            if (pool) {
              const current_msg = next[agent.id].message
              const others = pool.filter(m => m !== current_msg)
              next[agent.id] = { ...next[agent.id], message: others[Math.floor(Math.random() * others.length)] }
            }
          }
        })
        return next
      })
    }, 3500)
    return () => clearInterval(timer)
  }, [agents])

  const activeCount = Object.values(display).filter(d => d.status === 'active' || d.status === 'processing').length

  return (
    <div className="p-4 flex flex-col gap-2">
      {/* Header row */}
      <div className="flex items-center justify-between" style={{ marginBottom: '4px' }}>
        <p style={{ color: '#94a3b8', fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
          Agent Pipeline
        </p>
        <span style={{
          fontSize: '0.65rem', color: '#22c55e', background: '#f0fdf4',
          border: '1px solid #bbf7d0', borderRadius: '99px', padding: '1px 8px',
        }}>
          {activeCount} running
        </span>
      </div>

      {/* Agent rows */}
      {agents.map((agent, i) => {
        const d = display[agent.id] ?? { message: agent.message, status: agent.status }
        return (
          <div
            key={agent.id}
            className="flex items-center gap-3 rounded-lg"
            style={{
              padding: '10px 12px',
              background: '#ffffff',
              border: '1px solid #e2e8f0',
              opacity: d.status === 'idle' ? 0.7 : 1,
              transition: 'opacity 0.3s',
            }}
          >
            {/* Step number */}
            <span style={{
              width: '18px', height: '18px', borderRadius: '50%',
              background: d.status === 'idle' ? '#f1f5f9' : '#ede9fe',
              color: d.status === 'idle' ? '#94a3b8' : '#6366f1',
              fontSize: '0.6rem', fontWeight: 700,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0,
            }}>
              {i + 1}
            </span>

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5">
                <p style={{ fontSize: '0.8rem', color: '#334155', fontWeight: 500 }}>{agent.label}</p>
                <HelpIcon text={AGENT_HELP[agent.id]} />
              </div>
              <p style={{
                fontSize: '0.7rem', color: '#64748b',
                whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
              }}>
                {d.message}
              </p>
            </div>

            <div className="flex items-center gap-1.5" style={{ flexShrink: 0 }}>
              <StatusDot status={d.status} />
              <span style={{ fontSize: '0.65rem', color: STATUS_COLOR[d.status] }}>
                {STATUS_LABEL[d.status]}
              </span>
            </div>
          </div>
        )
      })}

      {/* Generate Report button — live mode only */}
      {isLive && (
        <button
          onClick={handleGenerateReport}
          disabled={reportLoading}
          style={{
            marginTop: '4px', width: '100%', padding: '10px',
            borderRadius: '8px', border: 'none', cursor: reportLoading ? 'not-allowed' : 'pointer',
            background: reportLoading ? '#e2e8f0' : '#0f172a',
            color: reportLoading ? '#94a3b8' : 'white',
            fontSize: '0.8rem', fontWeight: 600,
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
            transition: 'background 0.15s',
          }}
        >
          {reportLoading ? (
            <>
              <span style={{
                width: '13px', height: '13px', borderRadius: '50%',
                border: '2px solid #94a3b8', borderTopColor: '#6366f1',
                animation: 'spin 0.7s linear infinite', display: 'inline-block',
              }} />
              Running all agents…
            </>
          ) : '📋 Generate Narrator Report'}
        </button>
      )}

      {reportError && (
        <p style={{ fontSize: '0.72rem', color: '#dc2626', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', padding: '10px 12px' }}>
          {reportError}
        </p>
      )}

      {/* Narrative report card */}
      {report && (
        <div style={{
          marginTop: '4px', background: '#f8fafc', border: '1px solid #e2e8f0',
          borderRadius: '10px', padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: '10px',
        }}>
          <p style={{ fontSize: '0.7rem', fontWeight: 700, color: '#334155', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            Narrator Report
          </p>
          {[
            { label: 'Executive Summary', key: 'executive_summary', color: '#1d4ed8' },
            { label: 'Technical Analysis', key: 'technical_analysis', color: '#7c3aed' },
            { label: 'Recommendations',   key: 'recommendations',   color: '#16a34a' },
            { label: 'Next Steps',        key: 'next_steps',        color: '#b45309' },
          ].map(({ label, key, color }) => (
            <div key={key}>
              <p style={{ fontSize: '0.65rem', fontWeight: 700, color, marginBottom: '3px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                {label}
              </p>
              <p style={{ fontSize: '0.72rem', color: '#475569', lineHeight: 1.5 }}>
                {report[key as keyof NarrativeReport]}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* CSS keyframe for pulse animation */}
      <style>{`
        @keyframes ping { 75%, 100% { transform: scale(2); opacity: 0; } }
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  )
}
