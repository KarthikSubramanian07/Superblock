import { useEffect, useRef, useState } from 'react'

interface TimeSliderProps {
  value: number
  onChange: (value: number) => void
}

const TICK_LABELS = ['6 AM', '9 AM', '12 PM', '3 PM', '6 PM', '10 PM']

function formatHour(h: number): string {
  if (h === 12) return '12 PM'
  if (h < 12) return `${h} AM`
  return `${h - 12} PM`
}

function prefersReducedMotion(): boolean {
  return typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

export default function TimeSlider({ value, onChange }: TimeSliderProps) {
  const [playing, setPlaying] = useState(false)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  // Keep a ref to current value so the interval callback always sees the latest hour
  const valueRef = useRef(value)
  useEffect(() => { valueRef.current = value }, [value])

  useEffect(() => {
    if (!playing) {
      if (intervalRef.current) clearInterval(intervalRef.current)
      return
    }
    // Autoplay longer than 5s needs a pause control (2.2.2) — play/pause button provides it.
    // Under reduced motion, advance once then stop instead of looping continuously.
    if (prefersReducedMotion()) {
      const next = valueRef.current >= 22 ? 6 : valueRef.current + 1
      onChange(next)
      setPlaying(false)
      return
    }
    intervalRef.current = setInterval(() => {
      const next = valueRef.current >= 22 ? 6 : valueRef.current + 1
      onChange(next)
    }, 900)
    return () => { if (intervalRef.current) clearInterval(intervalRef.current) }
  }, [playing, onChange])

  function handleScrub(v: number) {
    setPlaying(false)
    onChange(v)
  }

  return (
    <div
      className="flex items-center gap-4 flex-shrink-0"
      style={{
        height: '60px',
        padding: '0 24px',
        background: '#ffffff',
        borderTop: '1px solid #e2e8f0',
      }}
      role="group"
      aria-label="Time of day"
    >
      {/* Play / Pause button */}
      <button
        type="button"
        onClick={() => setPlaying(p => !p)}
        aria-pressed={playing}
        aria-label={playing ? 'Pause time animation' : 'Play day timeline'}
        style={{
          width: '32px', height: '32px', minWidth: 32, minHeight: 32, borderRadius: '50%',
          background: playing ? '#4f46e5' : '#f1f5f9',
          border: playing ? 'none' : '1px solid #e2e8f0',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          cursor: 'pointer', flexShrink: 0, transition: 'background 0.15s',
        }}
        title={playing ? 'Pause' : 'Play day'}
      >
        {playing ? (
          <svg width="12" height="12" viewBox="0 0 12 12" fill="white" aria-hidden="true">
            <rect x="1" y="1" width="3.5" height="10" rx="1" />
            <rect x="7.5" y="1" width="3.5" height="10" rx="1" />
          </svg>
        ) : (
          <svg width="12" height="12" viewBox="0 0 12 12" fill="#4f46e5" aria-hidden="true">
            <polygon points="2,1 11,6 2,11" />
          </svg>
        )}
      </button>

      {/* Current time label */}
      <span
        style={{ color: '#475569', fontSize: '0.75rem', width: '52px', flexShrink: 0, fontVariantNumeric: 'tabular-nums' }}
        aria-live="polite"
      >
        {formatHour(value)}
      </span>

      {/* Slider + tick marks */}
      <div className="flex-1">
        <label htmlFor="time-of-day-slider" className="sr-only">
          Hour of day, 6 AM to 10 PM
        </label>
        <input
          id="time-of-day-slider"
          type="range"
          min={6}
          max={22}
          value={value}
          onChange={e => handleScrub(Number(e.target.value))}
          className="w-full cursor-pointer"
          style={{ accentColor: '#4f46e5' }}
          aria-valuetext={formatHour(value)}
        />
        <div className="flex justify-between" style={{ marginTop: '2px' }} aria-hidden="true">
          {TICK_LABELS.map(label => (
            <span key={label} style={{ color: '#64748b', fontSize: '0.65rem' }}>
              {label}
            </span>
          ))}
        </div>
      </div>

      {/* Loop indicator */}
      {playing && (
        <span style={{ color: '#4338ca', fontSize: '0.65rem', flexShrink: 0 }}>
          looping
        </span>
      )}
    </div>
  )
}
