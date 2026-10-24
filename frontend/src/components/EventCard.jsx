import { format } from 'date-fns'
import { MapPin, Calendar, Tag, User } from 'lucide-react'
import { useWebSocket } from '../hooks/useWebSocket'
import { useAuth } from '../context/AuthContext'
import { useState, useCallback } from 'react'

function statusBadge(s) {
  const map = {
    Published: 'badge-published',
    Draft: 'badge-draft',
    Cancelled: 'badge-cancelled',
    Completed: 'badge-completed',
  }
  return map[s] || 'badge-draft'
}

export default function EventCard({ event: initEvent, onClick }) {
  const [event, setEvent] = useState(initEvent)
  const { user } = useAuth()

  const handleWS = useCallback((msg) => {
    if (msg.type === 'ticket_update' && msg.event_id === event.id) {
      setEvent(prev => ({ ...prev, available_tickets: msg.available_tickets }))
    }
  }, [event.id])

  useWebSocket(`/ws/events/${event.id}`, handleWS)

  const soldOut = event.available_tickets === 0
  const isMyEvent = user && (user.id === event.organizer_id || (event.organizer_email && user.email === event.organizer_email))

  return (
    <div className="event-card" onClick={onClick} role="button" tabIndex={0}
      onKeyDown={e => e.key === 'Enter' && onClick()}>
      {/* Header strip */}
      <div style={{
        background: isMyEvent ? 'linear-gradient(135deg, var(--primary), var(--secondary))' : 'linear-gradient(135deg, rgba(108,99,255,.25), rgba(247,183,49,.1))',
        height: 6,
      }} />

      <div className="event-card-body">
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '.4rem', gap: '.4rem', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', gap: '.35rem', alignItems: 'center' }}>
            <span className={`badge ${statusBadge(event.status)}`}>{event.status}</span>
            {isMyEvent && (
              <span className="badge badge-published" style={{ background: 'var(--primary)', color: '#fff', fontSize: '.7rem', fontWeight: 700 }}>
                Your Event
              </span>
            )}
          </div>
          <span className="live-pill">
            <span className="live-dot" />
            LIVE
          </span>
        </div>

        <div className="event-card-title">{event.title}</div>

        <div className="event-card-meta">
          <span style={{ display: 'flex', alignItems: 'center', gap: '.25rem' }}>
            <Calendar size={12} /> {format(new Date(event.event_date), 'MMM d, yyyy · h:mm a')}
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '.25rem' }}>
            <MapPin size={12} /> {event.venue}
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '.25rem', color: isMyEvent ? 'var(--primary)' : 'inherit', fontWeight: isMyEvent ? 600 : 400 }}>
            <User size={12} /> {isMyEvent ? 'Organized by you' : (event.organizer_email ? `By ${event.organizer_email}` : 'Organizer')}
          </span>
          {event.category && (
            <span style={{ display: 'flex', alignItems: 'center', gap: '.25rem' }}>
              <Tag size={12} /> {event.category}
            </span>
          )}
        </div>

        <div className="event-card-footer">
          <div>
            <div style={{ fontWeight: 700, fontSize: '1rem' }}>
              {event.ticket_price === 0 ? 'Free' : `$${Number(event.ticket_price).toFixed(2)}`}
            </div>
            <div className="ticket-count">
              <strong style={{ color: soldOut ? 'var(--danger)' : 'var(--success)' }}>
                {soldOut ? 'Sold out' : `${event.available_tickets}`}
              </strong>
              {!soldOut && ' tickets left'}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
