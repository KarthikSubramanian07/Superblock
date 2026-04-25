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

export default function TimeSlider({ value, onChange }: TimeSliderProps) {
  return (
    <div
      className="flex items-center gap-4 flex-shrink-0"
      style={{
        height: '60px',
        padding: '0 24px',
        background: '#ffffff',
        borderTop: '1px solid #e2e8f0',
      }}
    >
      <span style={{ color: '#64748b', fontSize: '0.75rem', width: '52px', flexShrink: 0 }}>
        {formatHour(value)}
      </span>
      <div className="flex-1">
        <input
          type="range"
          min={6}
          max={22}
          value={value}
          onChange={e => onChange(Number(e.target.value))}
          className="w-full cursor-pointer"
          style={{ accentColor: '#6366f1' }}
        />
        <div className="flex justify-between" style={{ marginTop: '2px' }}>
          {TICK_LABELS.map(label => (
            <span key={label} style={{ color: '#94a3b8', fontSize: '0.65rem' }}>
              {label}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}
