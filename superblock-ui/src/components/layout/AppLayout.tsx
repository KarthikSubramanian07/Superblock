import { useStore } from '@/store/useStore'
import Header from './Header'
import Sidebar from './Sidebar'
import TimeSlider from '@/components/controls/TimeSlider'
import MapView from '@/components/map/MapView'

export default function AppLayout() {
  const isDemoMode = useStore(s => s.isDemoMode)
  const toggleDemoMode = useStore(s => s.toggleDemoMode)
  const activeTab = useStore(s => s.activeTab)
  const setActiveTab = useStore(s => s.setActiveTab)
  const timeIndex = useStore(s => s.timeIndex)
  const setTimeIndex = useStore(s => s.setTimeIndex)

  return (
    <div className="flex flex-col h-screen overflow-hidden" style={{ background: '#f1f4f9', color: '#0f172a' }}>
      <Header isDemoMode={isDemoMode} onToggleDemo={toggleDemoMode} />
      <main className="flex flex-1 overflow-hidden">
        <MapView />
        <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
      </main>
      <TimeSlider value={timeIndex} onChange={setTimeIndex} />
    </div>
  )
}
