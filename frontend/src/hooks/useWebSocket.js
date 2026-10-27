import { useEffect, useRef, useState } from 'react'

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000/api/v1'

function buildWsUrl(path, token) {
  if (!path) return null
  const normalizedPath = path.startsWith('ws://') || path.startsWith('wss://') ? path : `${WS_BASE_URL}${path}`
  const suffix = token ? `?token=${encodeURIComponent(token)}` : ''
  return `${normalizedPath}${suffix}`
}

export function useWebSocket(path, onMessage, enabled = true) {
  const [status, setStatus] = useState('offline')
  const wsRef = useRef(null)
  const reconnectTimeout = useRef(null)
  const onMessageRef = useRef(onMessage)

  useEffect(() => {
    onMessageRef.current = onMessage
  })

  useEffect(() => {
    if (!enabled || !path) {
      setStatus('offline')
      return undefined
    }

    const accessToken = localStorage.getItem('access_token')
    let timeoutMs = 1000

    const connect = () => {
      const ws = new WebSocket(buildWsUrl(path, accessToken))
      wsRef.current = ws
      setStatus('live')

      ws.onopen = () => {
        setStatus('live')
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (typeof onMessageRef.current === 'function') {
            onMessageRef.current(data)
          }
        } catch {
          // malformed frames are ignored as required by the backend contract
        }
      }

      ws.onclose = (event) => {
        if (event.code === 1008) {
          setStatus('offline')
          return
        }

        setStatus('reconnecting')
        reconnectTimeout.current = setTimeout(() => {
          timeoutMs = Math.min(timeoutMs * 2, 30000)
          connect()
        }, timeoutMs)
      }

      ws.onerror = () => {
        setStatus('reconnecting')
      }
    }

    connect()

    const pingInterval = setInterval(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send('ping')
      }
    }, 25000)

    return () => {
      clearInterval(pingInterval)
      clearTimeout(reconnectTimeout.current)
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [enabled, path])

  return status
}

export function useNotificationsSocket() {
  return useWebSocket('/ws/notifications', (msg) => {
    if (msg && (msg.type === 'NEW_NOTIFICATION' || msg.type === 'notification')) {
      window.dispatchEvent(new CustomEvent('eventdesk:new-notification', { detail: msg }))
    }
  }, !!localStorage.getItem('access_token'))
}

export function useEventTicketsSocket(eventId) {
  const [flash, setFlash] = useState(false)

  const handle = (msg) => {
    if (msg && msg.type === 'TICKET_UPDATE') {
      window.dispatchEvent(new CustomEvent('eventdesk:ticket-update', { detail: msg }))
      setFlash(true)
      window.setTimeout(() => setFlash(false), 1200)
    }
  }

  useWebSocket(`/ws/events/${eventId}`, handle, Boolean(eventId))

  return flash
}
