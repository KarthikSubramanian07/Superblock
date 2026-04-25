import type { Tile } from '@/types'

const WS_URL = (import.meta.env.VITE_WS_URL as string | undefined) ?? 'ws://localhost:8000/ws/tiles'

export interface TileSocket {
  close: () => void
}

export function createTileSocket(
  onTiles: (tiles: Tile[]) => void,
  onStatusChange: (connected: boolean) => void,
): TileSocket {
  let ws: WebSocket | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let closed = false

  function connect() {
    try {
      ws = new WebSocket(WS_URL)
    } catch {
      onStatusChange(false)
      scheduleReconnect()
      return
    }

    ws.onopen = () => onStatusChange(true)

    ws.onmessage = (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data as string)
        const tiles: Tile[] = Array.isArray(data) ? data : (data as { tiles: Tile[] }).tiles
        if (tiles?.length) onTiles(tiles)
      } catch { /* ignore malformed frames */ }
    }

    ws.onclose = () => {
      onStatusChange(false)
      if (!closed) scheduleReconnect()
    }

    ws.onerror = () => {
      onStatusChange(false)
    }
  }

  function scheduleReconnect() {
    if (closed) return
    const delay = Number(import.meta.env.VITE_WS_RECONNECT_MS ?? 5000)
    reconnectTimer = setTimeout(connect, delay)
  }

  connect()

  return {
    close() {
      closed = true
      if (reconnectTimer) clearTimeout(reconnectTimer)
      ws?.close()
    },
  }
}
