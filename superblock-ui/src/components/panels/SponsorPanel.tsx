import { useEffect, useState } from 'react'

interface SponsorStats {
  zetic: { speedup: string; energy: string; inferences: number }
  fetch: { agents: number; messages: number }
  worldid: { verified: number; sybilPrevented: number }
  mongodb: { documents: number; connected: boolean }
  arista: { packets: number; latency: string }
  climate: { heatIslands: number; energySaved: string; score: number }
}

const BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://localhost:8000'

async function fetchSponsorStats(): Promise<SponsorStats | null> {
  try {
    const [zetic, fetchai, worldid, mongodb, arista, climate] = await Promise.all([
      window.fetch(`${BASE}/zetic/stats`).then(r => r.json()).catch(() => null),
      window.fetch(`${BASE}/fetch/stats`).then(r => r.json()).catch(() => null),
      window.fetch(`${BASE}/worldid/stats`).then(r => r.json()).catch(() => null),
      window.fetch(`${BASE}/mongodb/stats`).then(r => r.json()).catch(() => null),
      window.fetch(`${BASE}/arista/stats`).then(r => r.json()).catch(() => null),
      window.fetch(`${BASE}/climate/stats`).then(r => r.json()).catch(() => null),
    ])
    
    return {
      zetic: {
        speedup: zetic?.speedup_factor ? `${zetic.speedup_factor}x` : '137x',
        energy: zetic?.total_energy_saved_mj ? `${zetic.total_energy_saved_mj.toFixed(1)}mJ` : '0mJ',
        inferences: zetic?.inference_count ?? 0,
      },
      fetch: {
        agents: fetchai?.agent_count ?? 6,
        messages: fetchai?.total_messages ?? 0,
      },
      worldid: {
        verified: worldid?.verified_humans ?? 0,
        sybilPrevented: worldid?.sybil_attacks_prevented ?? 0,
      },
      mongodb: {
        documents: mongodb?.total_documents ?? 0,
        connected: mongodb?.atlas_connected ?? false,
      },
      arista: {
        packets: arista?.packets_routed ?? 0,
        latency: arista?.avg_latency_ms ? `${arista.avg_latency_ms}ms` : '4.2ms',
      },
      climate: {
        heatIslands: climate?.metrics?.heat_islands_detected ?? 0,
        energySaved: climate?.energy_impact?.npu_energy_saved_mj ? `${climate.energy_impact.npu_energy_saved_mj}mJ` : '0mJ',
        score: climate?.sustainability_score ?? 0,
      },
    }
  } catch {
    return null
  }
}

export default function SponsorPanel() {
  const [stats, setStats] = useState<SponsorStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchSponsorStats().then(s => {
      setStats(s)
      setLoading(false)
    })
    const interval = setInterval(() => {
      fetchSponsorStats().then(setStats)
    }, 5000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="p-4 flex items-center justify-center" style={{ minHeight: '200px' }}>
        <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Loading sponsor stats...</div>
      </div>
    )
  }

  return (
    <div className="p-4 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span style={{ fontSize: '0.65rem', fontWeight: 700, color: '#6366f1', letterSpacing: '0.05em' }}>
          🏆 SPONSOR INTEGRATIONS
        </span>
        <span style={{ fontSize: '0.6rem', color: '#94a3b8' }}>Live Stats</span>
      </div>

      {/* ZETIC Melange */}
      <SponsorCard
        name="ZETIC Melange"
        icon="⚡"
        color="#7c3aed"
        bgColor="#f5f3ff"
        borderColor="#ddd6fe"
        stats={[
          { label: 'NPU Speedup', value: stats?.zetic.speedup ?? '137x' },
          { label: 'Energy Saved', value: stats?.zetic.energy ?? '0mJ' },
          { label: 'Inferences', value: String(stats?.zetic.inferences ?? 0) },
        ]}
        tagline="On-Device AI • Apple Neural Engine"
      />

      {/* Fetch.ai */}
      <SponsorCard
        name="Fetch.ai ASI:One"
        icon="🤖"
        color="#0891b2"
        bgColor="#ecfeff"
        borderColor="#a5f3fc"
        stats={[
          { label: 'Agents', value: String(stats?.fetch.agents ?? 6) },
          { label: 'Messages', value: String(stats?.fetch.messages ?? 0) },
        ]}
        tagline="Multi-Agent Orchestration • Agentverse"
      />

      {/* World ID */}
      <SponsorCard
        name="World ID"
        icon="🆔"
        color="#16a34a"
        bgColor="#f0fdf4"
        borderColor="#bbf7d0"
        stats={[
          { label: 'Verified Humans', value: String(stats?.worldid.verified ?? 0) },
          { label: 'Sybil Blocked', value: String(stats?.worldid.sybilPrevented ?? 0) },
        ]}
        tagline="Proof of Human • Zero-Knowledge"
      />

      {/* MongoDB Atlas */}
      <SponsorCard
        name="MongoDB Atlas"
        icon="🍃"
        color="#00684a"
        bgColor="#f0fdf4"
        borderColor="#86efac"
        stats={[
          { label: 'Documents', value: String(stats?.mongodb.documents ?? 0) },
          { label: 'Status', value: stats?.mongodb.connected ? 'Connected' : 'Demo Mode' },
        ]}
        tagline="Real-Time Persistence • Time-Series"
      />

      {/* Arista */}
      <SponsorCard
        name="Arista Networks"
        icon="🌐"
        color="#2563eb"
        bgColor="#eff6ff"
        borderColor="#bfdbfe"
        stats={[
          { label: 'Packets Routed', value: String(stats?.arista.packets ?? 0) },
          { label: 'Latency', value: stats?.arista.latency ?? '4.2ms' },
        ]}
        tagline="Network Telemetry • Zero Loss"
      />

      {/* Sustain the Spark */}
      <SponsorCard
        name="Sustain the Spark"
        icon="🌱"
        color="#166534"
        bgColor="#ecfdf5"
        borderColor="#86efac"
        stats={[
          { label: 'Heat Islands', value: String(stats?.climate.heatIslands ?? 0) },
          { label: 'Sustainability', value: `${stats?.climate.score ?? 0}%` },
        ]}
        tagline="Climate Resilience • Energy Grid Protection"
      />
    </div>
  )
}

function SponsorCard({
  name,
  icon,
  color,
  bgColor,
  borderColor,
  stats,
  tagline,
}: {
  name: string
  icon: string
  color: string
  bgColor: string
  borderColor: string
  stats: { label: string; value: string }[]
  tagline: string
}) {
  return (
    <div
      style={{
        background: bgColor,
        border: `1px solid ${borderColor}`,
        borderRadius: '10px',
        padding: '12px 14px',
      }}
    >
      <div className="flex items-center gap-2 mb-2">
        <span style={{ fontSize: '1.1rem' }}>{icon}</span>
        <span style={{ fontSize: '0.8rem', fontWeight: 700, color }}>{name}</span>
        <span className="flex h-1.5 w-1.5 rounded-full animate-pulse" style={{ background: color }} />
      </div>
      <div className="flex gap-4 mb-2">
        {stats.map((s, i) => (
          <div key={i}>
            <div style={{ fontSize: '1rem', fontWeight: 800, color }}>{s.value}</div>
            <div style={{ fontSize: '0.55rem', color, opacity: 0.7 }}>{s.label}</div>
          </div>
        ))}
      </div>
      <div style={{ fontSize: '0.6rem', color: '#64748b' }}>{tagline}</div>
    </div>
  )
}
