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
  { color: 'rgba(120,210,140,0.85)', label: 'Low  (< 0.3)', textCue: 'L' },
  { color: 'rgba(255,208,60,0.85)',  label: 'Moderate  (0.3–0.5)', textCue: 'M' },
  { color: 'rgba(255,145,55,0.85)', label: 'High  (0.5–0.7)', textCue: 'H' },
  { color: 'rgba(225,75,75,0.85)',  label: 'Critical  (> 0.7)', textCue: 'C' },
]

// Hotspot centre points for pulsing markers
const HOTSPOT_POINTS = getMockHotspotIds().map(id => {
  const hs = getMockHotspot(id)
  const [lat, lng] = cellToLatLng(id)
  return { id, position: [lng, lat] as [number, number], label: hs?.location_label ?? '' }
})

const ACCESSIBLE_VIEWPORT = 'width=device-width, initial-scale=1'

function restoreViewportMeta() {
  const metas = document.querySelectorAll('meta[name="viewport"]')
  metas.forEach(meta => {
    const content = meta.getAttribute('content') || ''
    if (/user-scalable\s*=\s*no/i.test(content) || /maximum-scale\s*=\s*1(\.0)?/i.test(content)) {
      meta.setAttribute('content', ACCESSIBLE_VIEWPORT)
    }
  })
}

export default function MapView() {
  const tiles         = useStore(s => s.tiles)
  const selectedHexId = useStore(s => s.selectedHexId)
  const setSelectedHex = useStore(s => s.setSelectedHex)
  const setActiveTab = useStore(s => s.setActiveTab)

  const prefersReducedMotion =
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches

  // Pulsing ring animation — radius oscillates 60 → 120m (paused when reduced motion)
  const [pulseRadius, setPulseRadius] = useState(90)
  const expandingRef = useRef(true)
  useEffect(() => {
    if (prefersReducedMotion) return
    const t = setInterval(() => {
      setPulseRadius(r => {
        if (r >= 120) expandingRef.current = false
        if (r <= 60)  expandingRef.current = true
        return expandingRef.current ? r + 4 : r - 4
      })
    }, 80)
    return () => clearInterval(t)
  }, [prefersReducedMotion])

  // Mapbox GL rewrites the viewport meta to disable zoom; restore it (1.4.4 / meta-viewport).
  useEffect(() => {
    restoreViewportMeta()
    const observer = new MutationObserver(restoreViewportMeta)
    observer.observe(document.head, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['content'],
    })
    const poll = window.setInterval(restoreViewportMeta, 1000)
    return () => {
      observer.disconnect()
      window.clearInterval(poll)
    }
  }, [])

  const layers = [
    // Stress heat zones
    new H3HexagonLayer<Tile>({
      id: 'stress-layer',
      data: tiles,
      getHexagon: d => d.h3_index,
      getFillColor: d => selectedHexId === d.h3_index ? [255, 255, 0, 200] : alsToColor(d.als_score), // Yellow highlight for selected
      getLineColor: d => selectedHexId === d.h3_index ? [0, 0, 0, 255] : [0, 0, 0, 0], // Black border for selected
      getLineWidth: d => selectedHexId === d.h3_index ? 2 : 0,
      extruded: false,
      stroked: true,
      filled: true,
      pickable: true,
      onClick: (info: PickingInfo<Tile>) => {
        if (info.object) setSelectedHex(info.object.h3_index)
      },
      updateTriggers: { getFillColor: [tiles, selectedHexId], getLineColor: selectedHexId, getLineWidth: selectedHexId },
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

  const selectedLabel = HOTSPOT_POINTS.find(p => p.id === selectedHexId)?.label
  const mapSummary = selectedHexId
    ? `Urban stress map. Selected zone${selectedLabel ? `: ${selectedLabel}` : ''}.`
    : 'Urban stress map of heat islands. Use the hotspot list below or the Hotspot panel to select a zone without the mouse.'

  return (
    <div
      style={{ width: '100%', height: '100%', position: 'relative' }}
      role="region"
      aria-label="Urban stress map"
    >
      <p id="map-summary" className="sr-only">{mapSummary}</p>
      <div
        style={{ width: '100%', height: '100%' }}
        role="img"
        aria-labelledby="map-summary"
      >
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
      </div>

      {/* Top-left hint */}
      <div
        style={{
          position: 'absolute', top: 12, left: 12,
          background: 'white', padding: '6px 12px', borderRadius: '8px',
          fontSize: '12px', color: '#334155',
          boxShadow: '0 2px 8px rgba(0,0,0,0.12)', border: '1px solid #e2e8f0',
          maxWidth: 'min(260px, calc(100% - 24px))',
        }}
        aria-hidden="true"
      >
        {selectedHexId ? 'Hotspot selected — see panel →' : 'Click a stress zone to explore'}
      </div>

      {/* Keyboard-accessible hotspot picker (map canvas itself is not keyboard operable) */}
      <div
        style={{
          position: 'absolute', top: 12, right: 12,
          background: 'white', padding: '8px 10px', borderRadius: '8px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.12)', border: '1px solid #e2e8f0',
          maxWidth: 'min(220px, calc(100% - 24px))',
          maxHeight: '40%',
          overflow: 'auto',
        }}
      >
        <p style={{ color: '#475569', margin: '0 0 6px', fontWeight: 600, fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
          Hotspots
        </p>
        <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: 4 }}>
          {HOTSPOT_POINTS.map(point => {
            const selected = selectedHexId === point.id
            return (
              <li key={point.id}>
                <button
                  type="button"
                  onClick={() => {
                    setSelectedHex(point.id)
                    setActiveTab('hotspot')
                  }}
                  aria-pressed={selected}
                  style={{
                    width: '100%', textAlign: 'left', minHeight: 28,
                    padding: '4px 8px', borderRadius: 6, cursor: 'pointer',
                    border: `1px solid ${selected ? '#4f46e5' : '#e2e8f0'}`,
                    background: selected ? '#eef2ff' : '#fff',
                    color: '#0f172a', fontSize: 11, fontWeight: selected ? 700 : 500,
                  }}
                >
                  {point.label || point.id}
                </button>
              </li>
            )
          })}
        </ul>
      </div>

      {/* Legend */}
      <div
        style={{
          position: 'absolute', bottom: 24, left: 12,
          background: 'white', padding: '10px 14px', borderRadius: '8px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)', border: '1px solid #e2e8f0', fontSize: '11px',
          maxWidth: 'min(240px, calc(100% - 24px))',
        }}
        aria-label="Stress level legend"
      >
        <p style={{ color: '#475569', marginBottom: '6px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginTop: 0 }}>
          Stress Level
        </p>
        {LEGEND.map(item => (
          <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: '7px', marginBottom: '3px' }}>
            <span
              aria-hidden="true"
              style={{
                width: '16px', height: '16px', borderRadius: '2px', background: item.color,
                display: 'inline-flex', flexShrink: 0, alignItems: 'center', justifyContent: 'center',
                fontSize: 9, fontWeight: 800, color: '#0f172a',
              }}
            >
              {item.textCue}
            </span>
            <span style={{ color: '#334155' }}>{item.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
