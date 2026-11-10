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
      className="sidebar-pane flex flex-col overflow-hidden flex-shrink-0"
      style={{
        background: '#ffffff',
        borderLeft: '1px solid #e2e8f0',
      }}
      aria-label="Analysis panels"
    >
      {/* Tab bar */}
      <div
        className="flex flex-shrink-0"
        style={{ borderBottom: '1px solid #e2e8f0' }}
        role="tablist"
        aria-label="Panel views"
      >
        {TABS.map(tab => {
          const selected = activeTab === tab.id
          return (
            <button
              key={tab.id}
              type="button"
              role="tab"
              id={`tab-${tab.id}`}
              aria-selected={selected}
              aria-controls={`panel-${tab.id}`}
              tabIndex={selected ? 0 : -1}
              onClick={() => onTabChange(tab.id)}
              onKeyDown={e => {
                const idx = TABS.findIndex(t => t.id === tab.id)
                if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
                  e.preventDefault()
                  const delta = e.key === 'ArrowRight' ? 1 : -1
                  const next = TABS[(idx + delta + TABS.length) % TABS.length]
                  onTabChange(next.id)
                  requestAnimationFrame(() => {
                    document.getElementById(`tab-${next.id}`)?.focus()
                  })
                } else if (e.key === 'Home') {
                  e.preventDefault()
                  onTabChange(TABS[0].id)
                  requestAnimationFrame(() => document.getElementById(`tab-${TABS[0].id}`)?.focus())
                } else if (e.key === 'End') {
                  e.preventDefault()
                  const last = TABS[TABS.length - 1]
                  onTabChange(last.id)
                  requestAnimationFrame(() => document.getElementById(`tab-${last.id}`)?.focus())
                }
              }}
              className="flex-1 py-3 transition-colors"
              style={{
                fontSize: '0.75rem',
                fontWeight: 500,
                minHeight: 44,
                borderBottom: selected ? '2px solid #4f46e5' : '2px solid transparent',
                color: selected ? '#4338ca' : '#64748b',
                marginBottom: '-1px',
                background: 'transparent',
                cursor: 'pointer',
              }}
            >
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* Panel content — key forces remount + fade on tab switch */}
      <div
        key={activeTab}
        id={`panel-${activeTab}`}
        role="tabpanel"
        aria-labelledby={`tab-${activeTab}`}
        className="flex-1 overflow-y-auto"
        style={{
          background: '#f8fafc',
          animation: 'fadeIn 0.18s ease',
        }}
      >
        {activeTab === 'agents' && <AgentPanel />}
        {activeTab === 'hotspot' && <HotspotPanel />}
        {activeTab === 'simulation' && <SimPanel />}
      </div>
      <style>{`@keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }`}</style>
    </aside>
  )
}
