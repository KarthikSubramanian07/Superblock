import {
  IDKitRequestWidget,
  type IDKitErrorCodes,
  type IDKitRequestHookConfig,
  type IDKitResult,
  useIDKitRequest,
} from '@worldcoin/idkit'
import { useStore } from '@/store/useStore'
import { useState } from 'react'

interface HeaderProps {
  isDemoMode: boolean
  isLive: boolean
  isConnecting: boolean
  onToggleDemo: () => void
}

export default function Header({ isDemoMode, isLive, isConnecting, onToggleDemo }: HeaderProps) {
  const isHumanVerified = useStore(s => s.isHumanVerified)
  const setHumanVerified = useStore(s => s.setHumanVerified)
  const [isOpen, setIsOpen] = useState(false)
  const [verifying, setVerifying] = useState(false)

  // IDKit v4 requires a signed RP context from a backend. Until that bridge exists,
  // keep a typed cast so the hackathon UI still builds and can open the widget shell.
  const config = {
    app_id: 'app_staging_5c60c91f_superblock',
    action: 'verify_citizen_sensor',
    preset: 'device',
    allow_legacy_proofs: true,
    environment: 'staging',
    rp_context: {
      rp_id: 'rp_demo_superblock',
      nonce: 'demo-nonce',
      created_at: 1_700_000_000,
      expires_at: 2_000_000_000,
      signature: 'demo-unsigned',
    },
  } as unknown as IDKitRequestHookConfig

  const { open } = useIDKitRequest(config)

  const postVerification = async (payload: Record<string, unknown>) => {
    const base = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://localhost:8000'
    const res = await fetch(`${base}/verify-human`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    const body = (await res.json()) as { success?: boolean }
    return res.ok && Boolean(body.success)
  }

  const handleVerify = async (result: IDKitResult) => {
    setVerifying(true)
    try {
      const ok = await postVerification(result as unknown as Record<string, unknown>)
      if (ok) {
        setHumanVerified(true)
        return
      }
      console.error('World ID server verification failed')
    } catch (err) {
      console.error('World ID server verification error', err)
    } finally {
      setVerifying(false)
    }
  }

  const handleDemoVerify = async () => {
    setVerifying(true)
    try {
      const ok = await postVerification({ is_mock: true })
      if (ok) setHumanVerified(true)
    } catch (err) {
      console.error('Demo World ID verification error', err)
    } finally {
      setVerifying(false)
    }
  }

  const handleError = (error: IDKitErrorCodes) => {
    console.error('World ID verification failed:', error)
  }

  const connectionLabel = isDemoMode
    ? 'Demo'
    : isConnecting
      ? 'Connecting'
      : isLive
        ? 'Live'
        : 'Demo (offline)'

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
      <div className="flex items-baseline gap-2 min-w-0">
        <h1 style={{ color: '#0f172a', fontWeight: 700, fontSize: '1.1rem', letterSpacing: '-0.02em', margin: 0 }}>
          SuperBlock
        </h1>
        <span style={{ color: '#64748b', fontSize: '0.7rem' }} className="hidden sm:inline">Urban Nervous System</span>
      </div>

      <div
        className="flex items-center gap-2 px-2 py-0.5 rounded-md ml-2 sm:ml-4"
        style={{ background: '#f5f3ff', border: '1px solid #ddd6fe' }}
        aria-label="ZETIC NPU available"
      >
        <span style={{ color: '#6d28d9', fontSize: '0.6rem', fontWeight: 800, letterSpacing: '0.05em' }}>ZETIC NPU</span>
        <span className="flex h-1.5 w-1.5 rounded-full bg-violet-500" aria-hidden="true" />
      </div>

      {/* World ID Verification */}
      {isHumanVerified ? (
        <div
          className="flex items-center gap-2 px-2 py-0.5 rounded-md"
          style={{ background: '#f0fdf4', border: '1px solid #bbf7d0' }}
          role="status"
        >
          <span style={{ color: '#15803d', fontSize: '0.6rem', fontWeight: 800, letterSpacing: '0.05em' }}>VERIFIED HUMAN</span>
          <span style={{ fontSize: '0.7rem' }} aria-hidden="true">🆔</span>
        </div>
      ) : (
        <>
          <button
            type="button"
            onClick={() => open()}
            disabled={verifying}
            style={{
              fontSize: '0.7rem', fontWeight: 700, padding: '6px 12px',
              minHeight: 32, borderRadius: '6px', background: '#000', color: '#fff',
              cursor: verifying ? 'wait' : 'pointer', border: 'none',
            }}
          >
            Verify with World ID
          </button>
          {isDemoMode && (
            <button
              type="button"
              onClick={() => { void handleDemoVerify() }}
              disabled={verifying}
              style={{
                fontSize: '0.7rem', fontWeight: 700, padding: '6px 12px',
                minHeight: 32, borderRadius: '6px', background: '#334155', color: '#fff',
                cursor: verifying ? 'wait' : 'pointer', border: 'none',
              }}
            >
              Demo verify
            </button>
          )}
          <IDKitRequestWidget
            open={isOpen}
            onOpenChange={setIsOpen}
            onSuccess={handleVerify}
            onError={handleError}
            {...config}
          />
        </>
      )}

      <div className="flex-1" />

      {/* Four-state badge: DEMO · CONNECTING… · OFFLINE · LIVE */}
      <div
        className="flex items-center gap-2 px-3 py-1 rounded-full"
        style={{
          background: isDemoMode
            ? '#fffbeb'
            : isConnecting
              ? '#eff6ff'
              : isLive
                ? '#f0fdf4'
                : '#f8fafc',
          border: `1px solid ${
            isDemoMode
              ? '#fde68a'
              : isConnecting
                ? '#bfdbfe'
                : isLive
                  ? '#bbf7d0'
                  : '#cbd5e1'
          }`,
        }}
        role="status"
        aria-label={`Connection status: ${connectionLabel}`}
      >
        <span
          aria-hidden="true"
          style={{
            width: isConnecting || isLive ? '8px' : '6px',
            height: isConnecting || isLive ? '8px' : '6px',
            borderRadius: '50%',
            background: isDemoMode
              ? '#d97706'
              : isConnecting
                ? '#2563eb'
                : isLive
                  ? '#15803d'
                  : '#64748b',
            display: 'inline-block',
            ...(isConnecting
              ? {
                  border: '2px solid #93c5fd',
                  borderTopColor: '#3b82f6',
                  background: 'transparent',
                  animation: 'spin 0.8s linear infinite',
                }
              : {}),
          }}
        />
        <span style={{
          color: isDemoMode
            ? '#92400e'
            : isConnecting
              ? '#1d4ed8'
              : isLive
                ? '#166534'
                : '#475569',
          fontSize: '0.7rem',
          fontWeight: 600,
        }}>
          {isDemoMode ? 'DEMO' : isConnecting ? 'CONNECTING…' : isLive ? 'LIVE' : 'DEMO'}
        </span>
        {!isDemoMode && !isConnecting && !isLive && (
          <span style={{ color: '#64748b', fontSize: '0.65rem' }}>(offline)</span>
        )}
        {isConnecting && <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>}
      </div>

      {/* Demo toggle */}
      <div className="flex items-center gap-2">
        <span style={{ color: '#64748b', fontSize: '0.7rem' }} className="hidden sm:block" aria-hidden="true">Demo</span>
        <button
          type="button"
          onClick={onToggleDemo}
          className="relative inline-flex items-center rounded-full transition-colors"
          style={{
            width: '44px',
            height: '28px',
            minWidth: '44px',
            minHeight: '28px',
            background: isDemoMode ? '#d97706' : '#94a3b8',
          }}
          aria-label={isDemoMode ? 'Demo mode on' : 'Demo mode off'}
          aria-pressed={isDemoMode}
        >
          <span
            className="inline-block rounded-full bg-white shadow transition-transform"
            aria-hidden="true"
            style={{
              width: '20px',
              height: '20px',
              transform: isDemoMode ? 'translateX(22px)' : 'translateX(4px)',
            }}
          />
        </button>
      </div>
    </header>
  )
}
