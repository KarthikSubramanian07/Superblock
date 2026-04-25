interface HeaderProps {
  isDemoMode: boolean
  onToggleDemo: () => void
}

export default function Header({ isDemoMode, onToggleDemo }: HeaderProps) {
  return (
    <header
      className="flex items-center px-5 gap-4 flex-shrink-0"
      style={{
        height: '56px',
        background: '#12141e',
        borderBottom: '1px solid #2a2d3a',
      }}
    >
      {/* Wordmark */}
      <div className="flex items-baseline gap-2">
        <span style={{ color: '#f1f5f9', fontWeight: 600, fontSize: '1.1rem', letterSpacing: '-0.02em' }}>
          SuperBlock
        </span>
        <span style={{ color: '#4b5563', fontSize: '0.7rem' }}>Urban Nervous System</span>
      </div>

      <div className="flex-1" />

      {/* Live / Demo badge */}
      {isDemoMode ? (
        <div
          className="flex items-center gap-2 px-3 py-1 rounded-full"
          style={{ background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.2)' }}
        >
          <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#f59e0b', display: 'inline-block' }} />
          <span style={{ color: '#f59e0b', fontSize: '0.7rem', fontWeight: 500 }}>DEMO</span>
        </div>
      ) : (
        <div
          className="flex items-center gap-2 px-3 py-1 rounded-full"
          style={{ background: 'rgba(34,197,94,0.1)', border: '1px solid rgba(34,197,94,0.2)' }}
        >
          <span className="relative flex" style={{ width: '8px', height: '8px' }}>
            <span
              className="animate-ping absolute inline-flex rounded-full"
              style={{ width: '100%', height: '100%', background: '#4ade80', opacity: 0.75 }}
            />
            <span
              className="relative inline-flex rounded-full"
              style={{ width: '8px', height: '8px', background: '#22c55e' }}
            />
          </span>
          <span style={{ color: '#22c55e', fontSize: '0.7rem', fontWeight: 500 }}>LIVE</span>
        </div>
      )}

      {/* Privacy badge */}
      <div
        className="items-center gap-1.5 px-3 py-1 rounded-full hidden sm:flex"
        style={{ background: '#1a1d2e', border: '1px solid #2a2d3a' }}
      >
        <span style={{ fontSize: '0.75rem' }}>🔒</span>
        <span style={{ color: '#6b7280', fontSize: '0.7rem' }}>Raw biometrics: on-device</span>
      </div>

      {/* Demo toggle */}
      <div className="flex items-center gap-2">
        <span style={{ color: '#4b5563', fontSize: '0.7rem' }} className="hidden sm:block">Demo</span>
        <button
          onClick={onToggleDemo}
          className="relative inline-flex items-center rounded-full transition-colors focus:outline-none"
          style={{
            width: '36px',
            height: '20px',
            background: isDemoMode ? '#f59e0b' : '#374151',
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
