import DeckGL from '@deck.gl/react'
import Map from 'react-map-gl/mapbox'
import { H3HexagonLayer } from '@deck.gl/geo-layers'
import { HeatmapLayer } from '@deck.gl/aggregation-layers'
import type { PickingInfo } from '@deck.gl/core'
import { cellToLatLng } from 'h3-js'
import 'mapbox-gl/dist/mapbox-gl.css'
import { useStore } from '@/store/useStore'
import { MAP_CENTER, MAP_ZOOM, MAPBOX_STYLE, ALS_RED_ZONE_THRESHOLD } from '@/lib/constants'
import type { Tile } from '@/types'

const INITIAL_VIEW_STATE = {
  longitude: MAP_CENTER[0],
  latitude: MAP_CENTER[1],
  zoom: MAP_ZOOM,
  pitch: 0,
  bearing: 0,
}

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN as string

// Green → lime → yellow → orange → red — matches the reference style
const HEATMAP_COLORS: [number, number, number][] = [
  [34,  197, 94],
  [132, 204, 22],
  [234, 179, 8],
  [249, 115, 22],
  [239, 68,  68],
  [185, 28,  28],
]

const LEGEND = [
  { color: '#22c55e', label: 'Low' },
  { color: '#eab308', label: 'Moderate' },
  { color: '#f97316', label: 'High' },
  { color: '#ef4444', label: 'Critical' },
]

interface HeatPoint {
  position: [number, number]
  weight: number
}

export default function MapView() {
  const tiles = useStore(s => s.tiles)
  const selectedHexId = useStore(s => s.selectedHexId)
  const setSelectedHex = useStore(s => s.setSelectedHex)

  // Convert H3 tiles to lat/lng points for the heatmap
  const heatPoints: HeatPoint[] = tiles.map(t => {
    const [lat, lng] = cellToLatLng(t.h3_index)
    return { position: [lng, lat], weight: t.als_score }
  })

  const layers = [
    // Smooth heatmap — the visual layer
    new HeatmapLayer<HeatPoint>({
      id: 'stress-heatmap',
      data: heatPoints,
      getPosition: d => d.position,
      getWeight: d => d.weight,
      radiusPixels: 80,
      intensity: 1.3,
      threshold: 0.03,
      colorRange: HEATMAP_COLORS,
      updateTriggers: {
        getWeight: tiles,
      },
    }),

    // Invisible H3 layer — click interaction only
    new H3HexagonLayer<Tile>({
      id: 'stress-interactive',
      data: tiles,
      getHexagon: d => d.h3_index,
      getFillColor: [0, 0, 0, 1],
      extruded: false,
      stroked: false,
      pickable: true,
      onClick: (info: PickingInfo<Tile>) => {
        if (info.object) setSelectedHex(info.object.h3_index)
      },
      updateTriggers: { data: tiles },
    }),

    // Red zone pulse ring — thin outline on critical tiles
    new H3HexagonLayer<Tile>({
      id: 'redzone-ring',
      data: tiles.filter(t => t.als_score > ALS_RED_ZONE_THRESHOLD),
      getHexagon: d => d.h3_index,
      getFillColor: [0, 0, 0, 0],
      getLineColor: [185, 28, 28, 200],
      lineWidthMinPixels: 2,
      extruded: false,
      stroked: true,
      filled: false,
      pickable: false,
      updateTriggers: { data: tiles },
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

      {/* Selected indicator */}
      {selectedHexId && (
        <div style={{
          position: 'absolute', top: 12, left: 12,
          background: 'white', padding: '6px 12px',
          borderRadius: '8px', fontSize: '12px', color: '#334155',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)', border: '1px solid #e2e8f0',
        }}>
          📍 Hotspot selected — see panel →
        </div>
      )}

      {/* Legend */}
      <div style={{
        position: 'absolute', bottom: 24, left: 12,
        background: 'white', padding: '10px 14px',
        borderRadius: '8px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        border: '1px solid #e2e8f0', fontSize: '11px',
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
