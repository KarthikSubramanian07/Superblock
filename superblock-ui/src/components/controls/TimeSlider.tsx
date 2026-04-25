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
        background: '#12141e',
        borderTop: '1px solid #2a2d3a',
      }}
    >
      <span style={{ color: '#6b7280', fontSize: '0.75rem', width: '52px', flexShrink: 0 }}>
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
            <span key={label} style={{ color: '#374151', fontSize: '0.65rem' }}>
              {label}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}
