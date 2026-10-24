import { useState, useEffect, useCallback, useRef } from 'react'
import { Bell, Check, CheckCheck } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { api } from '../api'
import { useToast } from '../context/ToastContext'
import { useAuth } from '../context/AuthContext'
import { useWebSocket } from '../hooks/useWebSocket'

const TYPE_ICONS = {
  booking:        '🎟️',
  review:         '⭐',
  cancellation:   '❌',
  event_reminder: '🔔',
  system:         '📢',
}

export default function NotificationsPage() {
  const { user } = useAuth()
  const { show } = useToast()
  const [items, setItems] = useState([])
  const [unread, setUnread] = useState(0)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all') // all | unread
  const [typeFilter, setTypeFilter] = useState('')
  const seenNotificationIds = useRef(new Set())

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const q = {
        ...(filter === 'unread' ? { is_read: false } : {}),
        ...(typeFilter ? { type: typeFilter } : {}),
        limit: 50,
      }
      const d = await api.listNotifications(q)
      seenNotificationIds.current = new Set(d.items.map((item) => item.id))
      setItems(d.items)
      setUnread(d.unread_count)
    } catch {}
    setLoading(false)
  }, [filter, typeFilter])

  useEffect(() => { load() }, [load])

  // Live notifications via WebSocket
  const handleWS = useCallback((msg) => {
    if (msg.type === 'notification' || msg.type === 'NEW_NOTIFICATION') {
      const item = msg.data || {
        id: msg.id,
        title: msg.title,
        message: msg.message,
        type: msg.notification_type,
        notification_type: msg.notification_type,
        created_at: msg.created_at || new Date().toISOString(),
        is_read: false,
      }
      if (item.id && seenNotificationIds.current.has(item.id)) return
      if (item.id) seenNotificationIds.current.add(item.id)
      if (typeFilter && (item.type || item.notification_type)?.toLowerCase() !== typeFilter.toLowerCase()) return
      setItems(prev => [item, ...prev])
      setUnread(c => c + 1)
      show(`🔔 ${item.title}: ${item.message}`, 'info')
    }
  }, [show, typeFilter])
  useWebSocket('/ws/notifications', handleWS, !!user)

  const handleRead = async (id) => {
    try {
      await api.markNotificationRead(id)
      setItems(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n))
      setUnread(c => Math.max(0, c - 1))
    } catch {}
  }

  const handleReadAll = async () => {
    try {
      await api.markAllNotificationsRead()
      setItems(prev => filter === 'unread' ? [] : prev.map(n => ({ ...n, is_read: true })))
      setUnread(0)
      show('All marked as read', 'success')
    } catch {}
  }

  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 700 }}>
        <div className="section-header">
          <div>
            <h1 className="section-title">Notifications</h1>
            {unread > 0 && (
              <span className="text-muted text-sm">{unread} unread</span>
            )}
          </div>
          <div className="flex-gap">
            <select
              className="form-control"
              aria-label="Notification type"
              value={typeFilter}
              onChange={event => setTypeFilter(event.target.value)}
            >
              <option value="">All types</option>
              <option value="Booking">Bookings</option>
              <option value="Review">Reviews</option>
              <option value="EventCancelled">Event cancellations</option>
              <option value="System">System</option>
              <option value="EventReminder">Event reminders</option>
            </select>
            <div className="tabs" style={{ margin: 0, border: 'none', gap: 0 }}>
              {['all', 'unread'].map(f => (
                <button key={f} className={`tab${filter === f ? ' active' : ''}`} onClick={() => setFilter(f)}>
                  {f === 'all' ? 'All' : 'Unread'}
                </button>
              ))}
            </div>
            {unread > 0 && (
              <button className="btn btn-ghost btn-sm" onClick={handleReadAll}>
                <CheckCheck size={14} /> Mark all read
              </button>
            )}
          </div>
        </div>

        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          {loading ? (
            <div className="spinner" />
          ) : items.length === 0 ? (
            <div className="empty-state" style={{ padding: '2.5rem' }}>
              <Bell size={36} color="var(--muted)" />
              <h3>All caught up</h3>
              <p>No {filter === 'unread' ? 'unread ' : ''}notifications</p>
            </div>
          ) : (
            items.map(n => (
              <div
                key={n.id}
                className={`notif-item${!n.is_read ? ' unread' : ''}`}
                onClick={() => !n.is_read && handleRead(n.id)}
                style={{ cursor: n.is_read ? 'default' : 'pointer' }}
              >
                <div className="notif-icon">
                  {TYPE_ICONS[(n.type || n.notification_type || '').toLowerCase()] || '🔔'}
                </div>
                <div className="notif-body">
                  <div className="notif-title">{n.title}</div>
                  <div className="notif-msg">{n.message}</div>
                  <div className="notif-time">
                    {formatDistanceToNow(new Date(n.created_at), { addSuffix: true })}
                  </div>
                </div>
                {!n.is_read && (
                  <div style={{ display: 'flex', alignItems: 'center' }}>
                    <div style={{ width: 8, height: 8, background: 'var(--primary)', borderRadius: '50%' }} />
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
