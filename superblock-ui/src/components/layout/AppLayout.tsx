import { useEffect, useRef } from 'react'
import { useStore } from '@/store/useStore'
import { useLiveData } from '@/hooks/useLiveData'
import { getMockHotspotIds } from '@/data/mock'
import { AUTO_SELECT_DELAY_MS } from '@/lib/config'
import Header from './Header'
import Sidebar from './Sidebar'
import TimeSlider from '@/components/controls/TimeSlider'
import MapView from '@/components/map/MapView'

export default function AppLayout() {
  useLiveData()

  const isDemoMode     = useStore(s => s.isDemoMode)
  const isLive         = useStore(s => s.isLive)
  const isConnecting   = useStore(s => s.isConnecting)
  const toggleDemoMode = useStore(s => s.toggleDemoMode)
  const activeTab      = useStore(s => s.activeTab)
  const setActiveTab   = useStore(s => s.setActiveTab)
  const timeIndex      = useStore(s => s.timeIndex)
  const setTimeIndex   = useStore(s => s.setTimeIndex)
  const setSelectedHex = useStore(s => s.setSelectedHex)

  // Auto-open the most critical hotspot on first load so judges see the full UI immediately
  const didInit = useRef(false)
  useEffect(() => {
    if (didInit.current) return
    didInit.current = true
    const ids = getMockHotspotIds()
    if (ids[0]) {
      setTimeout(() => {
        setSelectedHex(ids[0])
      }, AUTO_SELECT_DELAY_MS)
    }
  }, [setSelectedHex])

  return (
    <div className="flex flex-col h-screen overflow-hidden" style={{ background: '#f1f4f9', color: '#0f172a' }}>
      <Header isDemoMode={isDemoMode} isLive={isLive} isConnecting={isConnecting} onToggleDemo={toggleDemoMode} />
      <main className="flex flex-1 overflow-hidden">
        <MapView />
        <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
      </main>
      <TimeSlider value={timeIndex} onChange={setTimeIndex} />
    </div>
  )
}
