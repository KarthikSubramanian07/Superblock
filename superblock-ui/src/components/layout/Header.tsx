import { useStore } from '@/store/useStore'

interface HeaderProps {
  isDemoMode: boolean
  isLive: boolean
  isConnecting: boolean
  onToggleDemo: () => void
}

export default function Header({ isDemoMode, isLive, isConnecting, onToggleDemo }: HeaderProps) {
  const isHumanVerified = useStore(s => s.isHumanVerified)
  const setHumanVerified = useStore(s => s.setHumanVerified)

  const handleWorldIDVerify = () => {
    // Demo mode: simulate World ID verification for hackathon judges
    console.log('World ID Demo Verification')
    setHumanVerified(true)
  }

  return (
    <header
      className="flex items-center px-5 gap-4 flex-shrink-0"
      style={{
        height: '56px',
        background: '#ffffff',
        borderBottom: '1px solid #e2e8f0',
      }}
    >
      {/* Wordmark */}
      <div className="flex items-baseline gap-2">
        <span style={{ color: '#0f172a', fontWeight: 700, fontSize: '1.1rem', letterSpacing: '-0.02em' }}>
          SuperBlock
        </span>
        <span style={{ color: '#94a3b8', fontSize: '0.7rem' }}>Urban Nervous System</span>
      </div>

      {/* ZETIC NPU Badge - Showcases on-device AI */}
      <div className="flex items-center gap-2 px-2 py-0.5 rounded-md ml-4" style={{ background: '#f5f3ff', border: '1px solid #ddd6fe' }}>
        <span style={{ color: '#7c3aed', fontSize: '0.6rem', fontWeight: 800, letterSpacing: '0.05em' }}>⚡ ZETIC NPU</span>
        <span style={{ color: '#a78bfa', fontSize: '0.55rem', fontWeight: 600 }}>137x faster</span>
        <span className="flex h-1.5 w-1.5 rounded-full bg-violet-500 animate-pulse" />
      </div>

      {/* Fetch.ai ASI:One Badge */}
      <div className="flex items-center gap-2 px-2 py-0.5 rounded-md" style={{ background: '#ecfeff', border: '1px solid #a5f3fc' }}>
        <span style={{ color: '#0891b2', fontSize: '0.6rem', fontWeight: 800, letterSpacing: '0.05em' }}>🤖 ASI:One</span>
        <span style={{ color: '#06b6d4', fontSize: '0.55rem', fontWeight: 600 }}>6 Agents</span>
      </div>

      {/* MongoDB Atlas Badge */}
      <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-md" style={{ background: '#f0fdf4', border: '1px solid #86efac' }}>
        <span style={{ color: '#166534', fontSize: '0.6rem', fontWeight: 800 }}>🍃 Atlas</span>
      </div>

      {/* World ID Verification */}
      {isHumanVerified ? (
        <div className="flex items-center gap-2 px-2 py-0.5 rounded-md" style={{ background: '#f0fdf4', border: '1px solid #bbf7d0' }}>
          <span style={{ color: '#16a34a', fontSize: '0.6rem', fontWeight: 800, letterSpacing: '0.05em' }}>VERIFIED HUMAN</span>
          <span style={{ fontSize: '0.7rem' }}>🆔</span>
        </div>
      ) : (
        <button
          onClick={handleWorldIDVerify}
          style={{
            fontSize: '0.65rem', fontWeight: 700, padding: '4px 12px',
            borderRadius: '6px', background: '#000', color: '#fff',
            cursor: 'pointer', border: 'none',
          }}
        >
          🆔 Verify with World ID
        </button>
      )}

      <div className="flex-1" />

      {/* Four-state badge: DEMO · CONNECTING… · OFFLINE · LIVE */}
      {isDemoMode ? (
        <div className="flex items-center gap-2 px-3 py-1 rounded-full" style={{ background: '#fffbeb', border: '1px solid #fde68a' }}>
          <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#f59e0b', display: 'inline-block' }} />
          <span style={{ color: '#b45309', fontSize: '0.7rem', fontWeight: 600 }}>DEMO</span>
        </div>
      ) : isConnecting ? (
        <div className="flex items-center gap-2 px-3 py-1 rounded-full" style={{ background: '#eff6ff', border: '1px solid #bfdbfe' }}>
          <span style={{
            width: '8px', height: '8px', borderRadius: '50%',
            border: '2px solid #93c5fd', borderTopColor: '#3b82f6',
            display: 'inline-block', animation: 'spin 0.8s linear infinite',
          }} />
          <span style={{ color: '#1d4ed8', fontSize: '0.7rem', fontWeight: 600 }}>CONNECTING…</span>
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </div>
      ) : isLive ? (
        <div className="flex items-center gap-2 px-3 py-1 rounded-full" style={{ background: '#f0fdf4', border: '1px solid #bbf7d0' }}>
          <span className="relative flex" style={{ width: '8px', height: '8px' }}>
            <span className="animate-ping absolute inline-flex rounded-full" style={{ width: '100%', height: '100%', background: '#4ade80', opacity: 0.75 }} />
            <span className="relative inline-flex rounded-full" style={{ width: '8px', height: '8px', background: '#16a34a' }} />
          </span>
          <span style={{ color: '#15803d', fontSize: '0.7rem', fontWeight: 600 }}>LIVE</span>
        </div>
      ) : (
        <div className="flex items-center gap-2 px-3 py-1 rounded-full" style={{ background: '#f8fafc', border: '1px solid #cbd5e1' }}>
          <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#94a3b8', display: 'inline-block' }} />
          <span style={{ color: '#64748b', fontSize: '0.7rem', fontWeight: 600 }}>DEMO</span>
          <span style={{ color: '#94a3b8', fontSize: '0.65rem' }}>(offline)</span>
        </div>
      )}

      {/* Demo toggle */}
      <div className="flex items-center gap-2">
        <span style={{ color: '#94a3b8', fontSize: '0.7rem' }} className="hidden sm:block">Demo</span>
        <button
          onClick={onToggleDemo}
          className="relative inline-flex items-center rounded-full transition-colors focus:outline-none"
          style={{
            width: '36px',
            height: '20px',
            background: isDemoMode ? '#f59e0b' : '#cbd5e1',
          }}
          aria-label="Toggle demo mode"
        >
          <span
            className="inline-block rounded-full bg-white shadow transition-transform"
            style={{
              width: '16px',
              height: '16px',
              transform: isDemoMode ? 'translateX(18px)' : 'translateX(2px)',
            }}
          />
        </button>
      </div>
    </header>
  )
}
