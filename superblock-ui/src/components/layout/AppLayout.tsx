import { useState } from 'react'
import type { ActiveTab } from '@/types'
import Header from './Header'
import Sidebar from './Sidebar'
import TimeSlider from '@/components/controls/TimeSlider'

export default function AppLayout() {
  const [isDemoMode, setIsDemoMode] = useState(true)
  const [activeTab, setActiveTab] = useState<ActiveTab>('agents')
  const [timeIndex, setTimeIndex] = useState(14)

  return (
    <div className="flex flex-col h-screen overflow-hidden" style={{ background: '#0f1117', color: '#f1f5f9' }}>
      <Header isDemoMode={isDemoMode} onToggleDemo={() => setIsDemoMode(d => !d)} />
      <main className="flex flex-1 overflow-hidden">
        <MapPlaceholder />
        <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
      </main>
      <TimeSlider value={timeIndex} onChange={setTimeIndex} />
    </div>
  )
}

function MapPlaceholder() {
  return (
    <div
      className="flex-1 relative flex items-center justify-center"
      style={{ background: '#0d1020' }}
    >
      <div
        className="absolute inset-0"
        style={{
          backgroundImage:
            'radial-gradient(circle at 50% 40%, rgba(99,102,241,0.07) 0%, transparent 60%)',
        }}
      />
      <div className="text-center z-10 select-none">
        <div className="text-5xl mb-4">🗺️</div>
        <p style={{ color: '#4b5563', fontSize: '0.875rem' }}>3D City Map</p>
        <p style={{ color: '#374151', fontSize: '0.75rem', marginTop: '0.25rem' }}>
          Loads in Module 5
        </p>
      </div>
    </div>
  )
}
