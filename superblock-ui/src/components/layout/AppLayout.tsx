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
  const selectedHotspot = useStore(s => s.selectedHotspot)
  const simRunning     = useStore(s => s.simRunning)
  const simResult      = useStore(s => s.simResult)

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

  const statusParts: string[] = []
  if (isDemoMode) statusParts.push('Demo mode on')
  else if (isConnecting) statusParts.push('Connecting to live data')
  else if (isLive) statusParts.push('Live data connected')
  else statusParts.push('Offline demo data')
  if (selectedHotspot) statusParts.push(`Hotspot selected: ${selectedHotspot.location_label}`)
  if (simRunning) statusParts.push('Simulation running')
  if (simResult) {
    statusParts.push(
      `Simulation complete: stress reduced from ${Math.round(simResult.als_before * 100)}% to ${Math.round(simResult.als_after * 100)}%`,
    )
  }

  return (
    <div className="app-shell">
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>
      <div className="sr-only" role="status" aria-live="polite" aria-atomic="true">
        {statusParts.join('. ')}
      </div>
      <Header isDemoMode={isDemoMode} isLive={isLive} isConnecting={isConnecting} onToggleDemo={toggleDemoMode} />
      <main id="main-content" className="app-main" tabIndex={-1}>
        <div className="map-pane">
          <MapView />
        </div>
        <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
      </main>
      <TimeSlider value={timeIndex} onChange={setTimeIndex} />
    </div>
  )
}
