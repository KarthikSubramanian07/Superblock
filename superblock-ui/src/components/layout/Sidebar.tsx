import type { ActiveTab } from '@/types'
import AgentPanel from '@/components/panels/AgentPanel'
import HotspotPanel from '@/components/panels/HotspotPanel'
import SimPanel from '@/components/panels/SimPanel'
import SponsorPanel from '@/components/panels/SponsorPanel'

interface SidebarProps {
  activeTab: ActiveTab
  onTabChange: (tab: ActiveTab) => void
}

const TABS: { id: ActiveTab; label: string }[] = [
  { id: 'agents', label: 'Agents' },
  { id: 'hotspot', label: 'Hotspot' },
  { id: 'simulation', label: 'Simulate' },
  { id: 'sponsors', label: '🏆 Prizes' },
]

export default function Sidebar({ activeTab, onTabChange }: SidebarProps) {
  return (
    <aside
      className="flex flex-col overflow-hidden flex-shrink-0"
      style={{
        width: '380px',
        background: '#ffffff',
        borderLeft: '1px solid #e2e8f0',
      }}
    >
      {/* Tab bar */}
      <div
        className="flex flex-shrink-0"
        style={{ borderBottom: '1px solid #e2e8f0' }}
      >
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className="flex-1 py-3 transition-colors focus:outline-none"
            style={{
              fontSize: '0.75rem',
              fontWeight: 500,
              borderBottom: activeTab === tab.id ? '2px solid #6366f1' : '2px solid transparent',
              color: activeTab === tab.id ? '#6366f1' : '#94a3b8',
              marginBottom: '-1px',
              background: 'transparent',
              cursor: 'pointer',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Panel content — key forces remount + fade on tab switch */}
      <div
        key={activeTab}
        className="flex-1 overflow-y-auto"
        style={{
          background: '#f8fafc',
          animation: 'fadeIn 0.18s ease',
        }}
      >
        {activeTab === 'agents' && <AgentPanel />}
        {activeTab === 'hotspot' && <HotspotPanel />}
        {activeTab === 'simulation' && <SimPanel />}
        {activeTab === 'sponsors' && <SponsorPanel />}
      </div>

      {/* Climate Impact Footer - Sustain the Spark */}
      <div
        className="flex-shrink-0 px-4 py-3"
        style={{
          background: 'linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 100%)',
          borderTop: '1px solid #bbf7d0',
        }}
      >
        <div className="flex items-center justify-between mb-2">
          <span style={{ fontSize: '0.65rem', fontWeight: 700, color: '#166534', letterSpacing: '0.05em' }}>
            🌱 SUSTAIN THE SPARK
          </span>
          <span style={{ fontSize: '0.6rem', color: '#16a34a', fontWeight: 600 }}>Climate Impact</span>
        </div>
        <div className="grid grid-cols-3 gap-2">
          <div className="text-center">
            <div style={{ fontSize: '1rem', fontWeight: 800, color: '#16a34a' }}>25mJ</div>
            <div style={{ fontSize: '0.55rem', color: '#4ade80' }}>Energy Saved</div>
          </div>
          <div className="text-center">
            <div style={{ fontSize: '1rem', fontWeight: 800, color: '#16a34a' }}>137x</div>
            <div style={{ fontSize: '0.55rem', color: '#4ade80' }}>NPU Efficiency</div>
          </div>
          <div className="text-center">
            <div style={{ fontSize: '1rem', fontWeight: 800, color: '#16a34a' }}>0%</div>
            <div style={{ fontSize: '0.55rem', color: '#4ade80' }}>Data Leaked</div>
          </div>
        </div>
      </div>
      <style>{`@keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }`}</style>
    </aside>
  )
}
