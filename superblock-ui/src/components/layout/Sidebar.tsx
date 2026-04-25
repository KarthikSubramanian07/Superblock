import type { ActiveTab } from '@/types'
import AgentPanel from '@/components/panels/AgentPanel'
import HotspotPanel from '@/components/panels/HotspotPanel'
import SimPanel from '@/components/panels/SimPanel'

interface SidebarProps {
  activeTab: ActiveTab
  onTabChange: (tab: ActiveTab) => void
}

const TABS: { id: ActiveTab; label: string }[] = [
  { id: 'agents', label: 'Agents' },
  { id: 'hotspot', label: 'Hotspot' },
  { id: 'simulation', label: 'Simulation' },
]

export default function Sidebar({ activeTab, onTabChange }: SidebarProps) {
  return (
    <aside
      className="flex flex-col overflow-hidden flex-shrink-0"
      style={{
        width: '380px',
        background: '#12141e',
        borderLeft: '1px solid #2a2d3a',
      }}
    >
      {/* Tab bar */}
      <div
        className="flex flex-shrink-0"
        style={{ borderBottom: '1px solid #2a2d3a' }}
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
              color: activeTab === tab.id ? '#f1f5f9' : '#6b7280',
              marginBottom: '-1px',
              background: 'transparent',
              cursor: 'pointer',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Panel content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'agents' && <AgentPanel />}
        {activeTab === 'hotspot' && <HotspotPanel />}
        {activeTab === 'simulation' && <SimPanel />}
      </div>
    </aside>
  )
}
