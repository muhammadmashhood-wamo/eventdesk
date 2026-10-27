import { useEffect, useRef, useState } from 'react'
import {
  WS_BASE_URL,
  getValidAccessToken,
  refreshTokens,
  getAccessToken,
  getRefreshToken,
} from '../api'

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
  const isCancelledRef = useRef(false)

  useEffect(() => {
    onMessageRef.current = onMessage
  })

  useEffect(() => {
    isCancelledRef.current = false

    if (!enabled || !path) {
      setStatus('offline')
      return undefined
    }

    const requiresAuth = path.includes('/notifications')
    let timeoutMs = 1000
    let retryCount = 0
    const maxRetries = 10
    let hasConnected = false

    const connect = async () => {
      if (isCancelledRef.current) return

      let token = null
      if (requiresAuth) {
        token = await getValidAccessToken()
        if (isCancelledRef.current) return
        if (!token) {
          setStatus('offline')
          return
        }
      } else {
        token = await getValidAccessToken()
      }

      if (isCancelledRef.current) return

      try {
        const ws = new WebSocket(buildWsUrl(path, token))
        wsRef.current = ws

        ws.onopen = () => {
          if (isCancelledRef.current) {
            ws.close()
            return
          }
          hasConnected = true
          retryCount = 0
          timeoutMs = 1000
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

        ws.onclose = async (event) => {
          if (isCancelledRef.current) return

          // 1008 = Policy Violation (rejected by backend auth)
          // 1006 without hasConnected on an authenticated route = handshake 403 Forbidden rejection
          const isAuthRejection =
            event.code === 1008 || (!hasConnected && event.code === 1006 && requiresAuth)

          if (isAuthRejection) {
            // Attempt to refresh token once before giving up
            try {
              const refreshed = await refreshTokens()
              if (refreshed?.access_token && !isCancelledRef.current) {
                reconnectTimeout.current = setTimeout(connect, 500)
                return
              }
            } catch {
              // Refresh token expired or invalid; stop reconnecting
            }
            setStatus('offline')
            return
          }

          if (retryCount >= maxRetries) {
            setStatus('offline')
            return
          }

          retryCount += 1
          setStatus('reconnecting')
          reconnectTimeout.current = setTimeout(() => {
            timeoutMs = Math.min(timeoutMs * 2, 30000)
            connect()
          }, timeoutMs)
        }

        ws.onerror = () => {
          if (!isCancelledRef.current) {
            setStatus('reconnecting')
          }
        }
      } catch {
        if (!isCancelledRef.current) {
          setStatus('reconnecting')
          reconnectTimeout.current = setTimeout(connect, timeoutMs)
        }
      }
    }

    connect()

    const pingInterval = setInterval(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send('ping')
      }
    }, 25000)

    return () => {
      isCancelledRef.current = true
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
  }, Boolean(getAccessToken() || getRefreshToken()))
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
