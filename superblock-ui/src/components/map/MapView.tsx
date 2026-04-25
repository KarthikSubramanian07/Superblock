import DeckGL from '@deck.gl/react'
import Map from 'react-map-gl/mapbox'
import { H3HexagonLayer } from '@deck.gl/geo-layers'
import type { PickingInfo } from '@deck.gl/core'
import 'mapbox-gl/dist/mapbox-gl.css'
import { useStore } from '@/store/useStore'
import { alsToColor, alsToLabel } from '@/lib/colorScale'
import { MAP_CENTER, MAP_ZOOM, MAPBOX_STYLE, ALS_RED_ZONE_THRESHOLD } from '@/lib/constants'
import type { Tile } from '@/types'

const INITIAL_VIEW_STATE = {
  longitude: MAP_CENTER[0],
  latitude: MAP_CENTER[1],
  zoom: MAP_ZOOM,
  pitch: 45,
  bearing: 0,
}

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN as string

const LEGEND = [
  { color: '#22c55e', label: 'Low (< 0.3)' },
  { color: '#eab308', label: 'Moderate (0.3–0.5)' },
  { color: '#f97316', label: 'High (0.5–0.7)' },
  { color: '#ef4444', label: 'Critical (> 0.7)' },
]

export default function MapView() {
  const tiles = useStore(s => s.tiles)
  const selectedHexId = useStore(s => s.selectedHexId)
  const setSelectedHex = useStore(s => s.setSelectedHex)

  const redZoneTiles = tiles.filter(t => t.als_score > ALS_RED_ZONE_THRESHOLD)

  const layers = [
    new H3HexagonLayer<Tile>({
      id: 'stress-layer',
      data: tiles,
      getHexagon: d => d.h3_index,
      getFillColor: d => alsToColor(d.als_score),
      getElevation: d => d.als_score * 500,
      elevationScale: 1,
      extruded: true,
      pickable: true,
      opacity: 0.88,
      onClick: (info: PickingInfo<Tile>) => {
        if (info.object) setSelectedHex(info.object.h3_index)
      },
      updateTriggers: {
        getFillColor: tiles,
        getElevation: tiles,
      },
    }),
    new H3HexagonLayer<Tile>({
      id: 'redzone-wireframe',
      data: redZoneTiles,
      getHexagon: d => d.h3_index,
      getFillColor: [239, 68, 68, 15] as [number, number, number, number],
      getElevation: d => d.als_score * 500,
      elevationScale: 1,
      extruded: true,
      wireframe: true,
      pickable: false,
      updateTriggers: {
        data: redZoneTiles,
      },
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
        getTooltip={(info: PickingInfo<Tile>) => {
          if (!info.object) return null
          const t = info.object
          return {
            html: `
              <div style="font-size:12px;line-height:1.8;font-family:system-ui">
                <strong style="color:#0f172a">ALS: ${t.als_score} — ${alsToLabel(t.als_score)}</strong><br/>
                <span style="color:#64748b">Noise: ${t.noise_db} dB &nbsp;|&nbsp; ${t.context}</span>
              </div>
            `,
            style: {
              background: 'white',
              padding: '8px 12px',
              borderRadius: '8px',
              boxShadow: '0 4px 12px rgba(0,0,0,0.12)',
              border: '1px solid #e2e8f0',
              pointerEvents: 'none',
            },
          }
        }}
      >
        <Map mapboxAccessToken={MAPBOX_TOKEN} mapStyle={MAPBOX_STYLE} />
      </DeckGL>

      {/* Selected hex indicator */}
      {selectedHexId && (
        <div
          style={{
            position: 'absolute',
            top: 12,
            left: 12,
            background: 'white',
            padding: '6px 12px',
            borderRadius: '8px',
            fontSize: '12px',
            color: '#334155',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            border: '1px solid #e2e8f0',
          }}
        >
          📍 Hotspot selected — see panel →
        </div>
      )}

      {/* Legend */}
      <div
        style={{
          position: 'absolute',
          bottom: 24,
          left: 12,
          background: 'white',
          padding: '10px 14px',
          borderRadius: '8px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          border: '1px solid #e2e8f0',
          fontSize: '11px',
        }}
      >
        <p style={{ color: '#64748b', marginBottom: '6px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Stress Level
        </p>
        {LEGEND.map(item => (
          <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: '7px', marginBottom: '3px' }}>
            <span
              style={{
                width: '10px',
                height: '10px',
                borderRadius: '2px',
                background: item.color,
                display: 'inline-block',
                flexShrink: 0,
              }}
            />
            <span style={{ color: '#475569' }}>{item.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
