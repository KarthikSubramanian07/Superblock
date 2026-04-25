import DeckGL from '@deck.gl/react'
import Map from 'react-map-gl/mapbox'
import { H3HexagonLayer } from '@deck.gl/geo-layers'
import type { PickingInfo } from '@deck.gl/core'
import 'mapbox-gl/dist/mapbox-gl.css'
import { useStore } from '@/store/useStore'
import { MAP_CENTER, MAP_ZOOM, MAPBOX_STYLE } from '@/lib/constants'
import { alsToColor } from '@/lib/colorScale'
import type { Tile } from '@/types'

const INITIAL_VIEW_STATE = {
  longitude: MAP_CENTER[0],
  latitude: MAP_CENTER[1],
  zoom: MAP_ZOOM,
  pitch: 0,
  bearing: 0,
}

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN as string

const LEGEND = [
  { color: 'rgba(120,210,140,0.85)', label: 'Low  (< 0.3)' },
  { color: 'rgba(255,208,60,0.85)',  label: 'Moderate  (0.3–0.5)' },
  { color: 'rgba(255,145,55,0.85)', label: 'High  (0.5–0.7)' },
  { color: 'rgba(225,75,75,0.85)',  label: 'Critical  (> 0.7)' },
]

export default function MapView() {
  const tiles = useStore(s => s.tiles)
  const selectedHexId = useStore(s => s.selectedHexId)
  const setSelectedHex = useStore(s => s.setSelectedHex)

  const layers = [
    new H3HexagonLayer<Tile>({
      id: 'stress-layer',
      data: tiles,
      getHexagon: d => d.h3_index,
      getFillColor: d => alsToColor(d.als_score),
      extruded: false,
      stroked: false,
      filled: true,
      pickable: true,
      onClick: (info: PickingInfo<Tile>) => {
        if (info.object) setSelectedHex(info.object.h3_index)
      },
      updateTriggers: { getFillColor: tiles },
    }),
  ]

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <DeckGL
        initialViewState={INITIAL_VIEW_STATE}
        controller={true}
        layers={layers}
        onClick={(info: PickingInfo) => {
          if (!info.object) setSelectedHex(null)
        }}
      >
        <Map mapboxAccessToken={MAPBOX_TOKEN} mapStyle={MAPBOX_STYLE} />
      </DeckGL>

      {selectedHexId && (
        <div style={{
          position: 'absolute', top: 12, left: 12,
          background: 'white', padding: '6px 12px', borderRadius: '8px',
          fontSize: '12px', color: '#334155',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)', border: '1px solid #e2e8f0',
        }}>
          Hotspot selected — see panel →
        </div>
      )}

      {/* Legend */}
      <div style={{
        position: 'absolute', bottom: 24, left: 12,
        background: 'white', padding: '10px 14px', borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)', border: '1px solid #e2e8f0', fontSize: '11px',
      }}>
        <p style={{ color: '#64748b', marginBottom: '6px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Stress Level
        </p>
        {LEGEND.map(item => (
          <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: '7px', marginBottom: '3px' }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '2px', background: item.color, display: 'inline-block', flexShrink: 0 }} />
            <span style={{ color: '#475569' }}>{item.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
