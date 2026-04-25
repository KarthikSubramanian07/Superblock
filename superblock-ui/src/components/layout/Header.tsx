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

      <div className="flex-1" />

      {/* Live / Demo badge */}
      {isDemoMode ? (
        <div
          className="flex items-center gap-2 px-3 py-1 rounded-full"
          style={{ background: '#fffbeb', border: '1px solid #fde68a' }}
        >
          <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#f59e0b', display: 'inline-block' }} />
          <span style={{ color: '#b45309', fontSize: '0.7rem', fontWeight: 600 }}>DEMO</span>
        </div>
      ) : (
        <div
          className="flex items-center gap-2 px-3 py-1 rounded-full"
          style={{ background: '#f0fdf4', border: '1px solid #bbf7d0' }}
        >
          <span className="relative flex" style={{ width: '8px', height: '8px' }}>
            <span
              className="animate-ping absolute inline-flex rounded-full"
              style={{ width: '100%', height: '100%', background: '#4ade80', opacity: 0.75 }}
            />
            <span
              className="relative inline-flex rounded-full"
              style={{ width: '8px', height: '8px', background: '#16a34a' }}
            />
          </span>
          <span style={{ color: '#15803d', fontSize: '0.7rem', fontWeight: 600 }}>LIVE</span>
        </div>
      )}

      {/* Privacy badge */}
      <div
        className="items-center gap-1.5 px-3 py-1 rounded-full hidden sm:flex"
        style={{ background: '#f8fafc', border: '1px solid #e2e8f0' }}
      >
        <span style={{ fontSize: '0.75rem' }}>🔒</span>
        <span style={{ color: '#64748b', fontSize: '0.7rem' }}>Raw biometrics: on-device</span>
      </div>

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
