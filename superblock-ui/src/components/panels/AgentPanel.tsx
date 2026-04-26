import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { useStore } from '@/store/useStore'
import { AGENT_HELP } from '@/data/agentHelp'
import { AGENT_MESSAGES } from '@/data/agentMessages'
import type { Agent } from '@/types'
import { runLivePipeline } from '@/lib/api'

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

type Evidence = {
  topHotspot: string
  predictedIntervention: string
  agentCallOrder: string[]
  timestamp: string
  coordinatorNarrative: string
}

const SPECIALIST_ORDER = ['ingestion', 'mapping', 'diagnosis', 'simulation', 'planner', 'narrator']

function normalizeAgentId(id: string): string {
  return id.replace(/_agent$/, '').trim().toLowerCase()
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

  const [pipelineRunning, setPipelineRunning] = useState(false)
  const [pipelineStepIndex, setPipelineStepIndex] = useState(-1)
  const [pipelineOrder, setPipelineOrder] = useState<string[]>([])
  const [pipelineError, setPipelineError] = useState<string | null>(null)
  const [coordinatorStatus, setCoordinatorStatus] = useState<Agent['status']>('idle')
  const [evidence, setEvidence] = useState<Evidence | null>(null)

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
          message: `Receiving ${ingestionStatus.packets_per_min} packets/min · ${ingestionStatus.sensors_online} sensors online`,
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
    if (pipelineRunning) return
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
  }, [agents, pipelineRunning])

  async function handleRunFullPipeline() {
    setPipelineError(null)
    setEvidence(null)
    setPipelineRunning(true)
    setPipelineStepIndex(-1)
    setCoordinatorStatus('idle')

    const response = await runLivePipeline(selectedHotspot?.h3_index ? { h3_index: selectedHotspot.h3_index } : undefined)

    if (!response) {
      setPipelineRunning(false)
      setCoordinatorStatus('error')
      setPipelineError('Unable to run pipeline. Check backend connectivity.')
      return
    }

    const normalized = (response.agent_call_order ?? [])
      .map(normalizeAgentId)
      .filter((id, idx, arr) => SPECIALIST_ORDER.includes(id) && arr.indexOf(id) === idx)

    const mergedOrder = [...normalized, ...SPECIALIST_ORDER.filter(id => !normalized.includes(id))]
    setPipelineOrder(mergedOrder)

    for (let i = 0; i < mergedOrder.length; i += 1) {
      setPipelineStepIndex(i)
      await new Promise(resolve => setTimeout(resolve, 500))
    }

    setCoordinatorStatus('processing')
    await new Promise(resolve => setTimeout(resolve, 500))
    setCoordinatorStatus('active')

    const topIntervention = response.ranked_plan?.ranked_interventions?.[0]
    const predictedIntervention =
      topIntervention?.scenario_name
      ?? topIntervention?.intervention_id
      ?? 'No intervention returned'

    const coordinatorNarrative =
      response.narrative_report?.executive_summary
      ?? response.narrative_report?.recommendations
      ?? 'Coordinator completed full 6-agent workflow and generated narrative output.'

    setEvidence({
      topHotspot: response.selected_h3_index,
      predictedIntervention,
      agentCallOrder: [...mergedOrder.map(id => `${id}_agent`), 'coordinator_agent'],
      timestamp: new Date().toISOString(),
      coordinatorNarrative,
    })

    setPipelineRunning(false)
  }

  async function handleCopyEvidence() {
    if (!evidence) return
    const text = [
      `Top Hotspot: ${evidence.topHotspot}`,
      `Predicted Intervention: ${evidence.predictedIntervention}`,
      `Agent Call Order: ${evidence.agentCallOrder.join(' -> ')}`,
      `Timestamp: ${evidence.timestamp}`,
      `Coordinator Narrative: ${evidence.coordinatorNarrative}`,
    ].join('\n')
    await navigator.clipboard.writeText(text)
  }

  function getPipelineState(agentId: string, fallback: { status: Agent['status']; message: string }) {
    if (!pipelineOrder.length && !pipelineRunning) return fallback
    const index = pipelineOrder.indexOf(agentId)
    if (index === -1) return fallback
    if (pipelineRunning && index === pipelineStepIndex) {
      return { status: 'processing' as const, message: 'Executing full pipeline step…' }
    }
    if (index <= pipelineStepIndex) {
      return { status: 'active' as const, message: 'Completed in full pipeline run' }
    }
    return { status: 'idle' as const, message: 'Queued for full pipeline run' }
  }

  const activeCount = Object.values(display).filter(d => d.status === 'active' || d.status === 'processing').length

  return (
    <div className="p-4 flex flex-col gap-2">
      {/* Header row */}
      <div className="flex items-center justify-between" style={{ marginBottom: '4px' }}>
        <p style={{ color: '#94a3b8', fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
          Agent Pipeline
        </p>
        <div className="flex items-center gap-2">
          <button
            onClick={handleRunFullPipeline}
            disabled={pipelineRunning}
            style={{
              fontSize: '0.65rem',
              color: '#312e81',
              background: pipelineRunning ? '#e2e8f0' : '#e0e7ff',
              border: '1px solid #c7d2fe',
              borderRadius: '99px',
              padding: '2px 10px',
              cursor: pipelineRunning ? 'not-allowed' : 'pointer',
            }}
          >
            {pipelineRunning ? 'Running…' : 'Run Full Pipeline'}
          </button>
          <span style={{
            fontSize: '0.65rem', color: '#22c55e', background: '#f0fdf4',
            border: '1px solid #bbf7d0', borderRadius: '99px', padding: '1px 8px',
          }}>
            {activeCount} running
          </span>
        </div>
      </div>

      {pipelineError && (
        <div
          style={{
            fontSize: '0.68rem',
            color: '#b91c1c',
            background: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '8px',
            padding: '8px 10px',
            marginBottom: '6px',
          }}
        >
          {pipelineError}
        </div>
      )}

      {/* Agent rows */}
      {agents.map((agent, i) => {
        const raw = display[agent.id] ?? { message: agent.message, status: agent.status }
        const d = getPipelineState(agent.id, raw)
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

      <div
        className="flex items-center gap-3 rounded-lg"
        style={{
          padding: '10px 12px',
          background: '#ffffff',
          border: '1px solid #e2e8f0',
          opacity: coordinatorStatus === 'idle' ? 0.7 : 1,
          transition: 'opacity 0.3s',
        }}
      >
        <span style={{
          width: '18px', height: '18px', borderRadius: '50%',
          background: coordinatorStatus === 'idle' ? '#f1f5f9' : '#ede9fe',
          color: coordinatorStatus === 'idle' ? '#94a3b8' : '#6366f1',
          fontSize: '0.6rem', fontWeight: 700,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexShrink: 0,
        }}>
          C
        </span>
        <div className="flex-1 min-w-0">
          <p style={{ fontSize: '0.8rem', color: '#334155', fontWeight: 500 }}>Coordinator Narrative</p>
          <p style={{ fontSize: '0.7rem', color: '#64748b', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {coordinatorStatus === 'processing'
              ? 'Synthesizing multi-agent output into final narrative…'
              : coordinatorStatus === 'active'
                ? 'Narrative synthesis complete'
                : 'Idle'}
          </p>
        </div>
        <div className="flex items-center gap-1.5" style={{ flexShrink: 0 }}>
          <StatusDot status={coordinatorStatus} />
          <span style={{ fontSize: '0.65rem', color: STATUS_COLOR[coordinatorStatus] }}>
            {STATUS_LABEL[coordinatorStatus]}
          </span>
        </div>
      </div>

      {evidence && (
        <div
          style={{
            marginTop: '8px',
            background: '#f8fafc',
            border: '1px solid #cbd5e1',
            borderRadius: '10px',
            padding: '10px',
          }}
        >
          <div className="flex items-center justify-between" style={{ marginBottom: '6px' }}>
            <p style={{ fontSize: '0.7rem', fontWeight: 700, color: '#334155', letterSpacing: '0.04em' }}>
              EVIDENCE PANEL
            </p>
            <button
              onClick={handleCopyEvidence}
              style={{
                fontSize: '0.65rem',
                color: '#1d4ed8',
                background: '#eff6ff',
                border: '1px solid #bfdbfe',
                borderRadius: '6px',
                padding: '2px 8px',
                cursor: 'pointer',
              }}
            >
              Copy
            </button>
          </div>
          <div style={{ fontSize: '0.68rem', color: '#475569', lineHeight: 1.5 }}>
            <div><strong>Top Hotspot:</strong> {evidence.topHotspot}</div>
            <div><strong>Predicted Intervention:</strong> {evidence.predictedIntervention}</div>
            <div><strong>Agent Call Order:</strong> {evidence.agentCallOrder.join(' → ')}</div>
            <div><strong>Timestamp:</strong> {evidence.timestamp}</div>
          </div>
        </div>
      )}

      {/* CSS keyframe for pulse animation */}
      <style>{`
        @keyframes ping {
          75%, 100% { transform: scale(2); opacity: 0; }
        }
      `}</style>
    </div>
  )
}
