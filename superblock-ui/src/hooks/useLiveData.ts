import { useEffect, useRef } from 'react'
import { useStore } from '@/store/useStore'
import { checkHealth, fetchLiveTiles, fetchLiveHotspots } from '@/lib/api'
import { createTileSocket } from '@/lib/socket'
import { getMockTilesAtIndex } from '@/data/mock'
import type { TileSocket } from '@/lib/socket'

const POLL_INTERVAL_MS = Number(import.meta.env.VITE_POLL_INTERVAL_MS ?? 30_000)

export function useLiveData() {
  const isDemoMode     = useStore(s => s.isDemoMode)
  const timeIndex      = useStore(s => s.timeIndex)
  const setIsLive      = useStore(s => s.setIsLive)
  const setIsConnecting = useStore(s => s.setIsConnecting)
  const setTiles       = useStore(s => s.setTiles)

  const socketRef   = useRef<TileSocket | null>(null)
  const pollRef     = useRef<ReturnType<typeof setInterval> | null>(null)
  const wsLiveRef   = useRef(false)

  // Clear all connections
  function teardown() {
    socketRef.current?.close()
    socketRef.current = null
    if (pollRef.current) clearInterval(pollRef.current)
    pollRef.current = null
    wsLiveRef.current = false
  }

  useEffect(() => {
    if (isDemoMode) {
      teardown()
      setIsLive(false)
      setIsConnecting(false)
      setTiles(getMockTilesAtIndex(timeIndex))
      return
    }

    // 1. Health check — show "Connecting…" while we probe the backend
    setIsConnecting(true)
    checkHealth().then(healthy => {
      setIsConnecting(false)
      if (!healthy) {
        setIsLive(false)
        return
      }

      // 2. Try WebSocket for live tile stream
      socketRef.current = createTileSocket(
        (tiles) => {
          wsLiveRef.current = true
          setIsLive(true)
          setTiles(tiles)
        },
        (connected) => {
          if (!connected && wsLiveRef.current) {
            wsLiveRef.current = false
            setIsLive(false)
          }
        },
      )

      // 3. REST polling as backup (runs alongside WS; WS takes priority via wsLiveRef)
      async function poll() {
        if (wsLiveRef.current) return // WS is live — skip REST
        const tiles = await fetchLiveTiles(timeIndex)
        if (tiles) {
          setIsLive(true)
          setTiles(tiles)
        } else {
          setIsLive(false)
          setTiles(getMockTilesAtIndex(timeIndex))
        }
      }

      poll()
      pollRef.current = setInterval(poll, POLL_INTERVAL_MS)

      // 4. Fetch live hotspot list once (enriches the store for future clicks)
      fetchLiveHotspots().then(hotspots => {
        if (hotspots?.length) useStore.getState().setLiveHotspots(hotspots)
      })
    })

    return teardown
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isDemoMode])

  // When the user scrubs the time slider in live mode, fetch that hour from REST
  useEffect(() => {
    if (isDemoMode || wsLiveRef.current) return
    fetchLiveTiles(timeIndex).then(tiles => {
      if (tiles) {
        setIsLive(true)
        setTiles(tiles)
      } else {
        setTiles(getMockTilesAtIndex(timeIndex))
      }
    })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [timeIndex, isDemoMode])
}
