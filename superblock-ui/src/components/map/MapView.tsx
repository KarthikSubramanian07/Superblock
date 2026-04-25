import { useEffect, useRef, useState } from 'react'
import DeckGL from '@deck.gl/react'
import Map from 'react-map-gl/mapbox'
import { H3HexagonLayer } from '@deck.gl/geo-layers'
import { ScatterplotLayer } from '@deck.gl/layers'
import type { PickingInfo } from '@deck.gl/core'
import { cellToLatLng } from 'h3-js'
import 'mapbox-gl/dist/mapbox-gl.css'
import { useStore } from '@/store/useStore'
import { MAP_CENTER, MAP_ZOOM, MAPBOX_STYLE } from '@/lib/constants'
import { alsToColor } from '@/lib/colorScale'
import { getMockHotspotIds, getMockHotspot } from '@/data/mock'
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

// Hotspot centre points for pulsing markers
const HOTSPOT_POINTS = getMockHotspotIds().map(id => {
  const hs = getMockHotspot(id)
  const [lat, lng] = cellToLatLng(id)
  return { id, position: [lng, lat] as [number, number], label: hs?.location_label ?? '' }
})

export default function MapView() {
  const tiles         = useStore(s => s.tiles)
  const selectedHexId = useStore(s => s.selectedHexId)
  const setSelectedHex = useStore(s => s.setSelectedHex)

  // Pulsing ring animation — radius oscillates 60 → 120m
  const [pulseRadius, setPulseRadius] = useState(60)
  const expandingRef = useRef(true)
  useEffect(() => {
    const t = setInterval(() => {
      setPulseRadius(r => {
        if (r >= 120) expandingRef.current = false
        if (r <= 60)  expandingRef.current = true
        return expandingRef.current ? r + 4 : r - 4
      })
    }, 80)
    return () => clearInterval(t)
  }, [])

  const layers = [
    // Stress heat zones
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

    // Pulsing outer ring on hotspot centres
    new ScatterplotLayer({
      id: 'hotspot-pulse',
      data: HOTSPOT_POINTS,
      getPosition: d => d.position,
      getRadius: pulseRadius,
      radiusUnits: 'meters',
      getFillColor: [220, 38, 38, 0],
      getLineColor: [220, 38, 38, 180],
      stroked: true,
      filled: true,
      lineWidthMinPixels: 2,
      pickable: false,
      updateTriggers: { getRadius: pulseRadius },
    }),

    // Solid centre dot on hotspot centres
    new ScatterplotLayer({
      id: 'hotspot-dot',
      data: HOTSPOT_POINTS,
      getPosition: d => d.position,
      getRadius: 18,
      radiusUnits: 'meters',
      getFillColor: [220, 38, 38, 220],
      stroked: false,
      pickable: false,
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

      {/* Top-left hint */}
      <div style={{
        position: 'absolute', top: 12, left: 12,
        background: 'white', padding: '6px 12px', borderRadius: '8px',
        fontSize: '12px', color: '#334155',
        boxShadow: '0 2px 8px rgba(0,0,0,0.12)', border: '1px solid #e2e8f0',
        transition: 'opacity 0.3s',
      }}>
        {selectedHexId ? 'Hotspot selected — see panel →' : 'Click a stress zone to explore'}
      </div>

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
