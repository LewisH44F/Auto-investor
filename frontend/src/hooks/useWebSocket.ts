import { useEffect, useRef, useCallback, useState } from 'react'

type WebSocketStatus = 'connecting' | 'connected' | 'disconnected' | 'error'

interface WebSocketMessage {
  type: string
  data: unknown
}

interface UseWebSocketOptions {
  onMessage?: (message: WebSocketMessage) => void
  onConnect?: () => void
  onDisconnect?: () => void
  reconnectDelay?: number
  maxReconnectAttempts?: number
}

export function useWebSocket(url: string | null, options: UseWebSocketOptions = {}) {
  const {
    onMessage,
    onConnect,
    onDisconnect,
    reconnectDelay = 3000,
    maxReconnectAttempts = 5,
  } = options

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectCount = useRef(0)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const [status, setStatus] = useState<WebSocketStatus>('disconnected')

  const connect = useCallback(() => {
    if (!url || wsRef.current?.readyState === WebSocket.OPEN) return

    setStatus('connecting')
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      setStatus('connected')
      reconnectCount.current = 0
      onConnect?.()
    }

    ws.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data) as WebSocketMessage
        onMessage?.(parsed)
      } catch {
        console.error('Failed to parse WebSocket message:', event.data)
      }
    }

    ws.onclose = () => {
      setStatus('disconnected')
      onDisconnect?.()
      wsRef.current = null

      if (reconnectCount.current < maxReconnectAttempts) {
        reconnectCount.current++
        reconnectTimer.current = setTimeout(connect, reconnectDelay)
      }
    }

    ws.onerror = () => {
      setStatus('error')
      ws.close()
    }
  }, [url, onMessage, onConnect, onDisconnect, reconnectDelay, maxReconnectAttempts])

  const disconnect = useCallback(() => {
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current)
    }
    reconnectCount.current = maxReconnectAttempts // prevent reconnect
    wsRef.current?.close()
  }, [maxReconnectAttempts])

  const send = useCallback((data: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
    }
  }, [])

  useEffect(() => {
    if (url) {
      connect()
    }
    return () => {
      disconnect()
    }
  }, [url, connect, disconnect])

  return { status, send, disconnect, connect }
}
