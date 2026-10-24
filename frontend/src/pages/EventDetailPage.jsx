import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { format } from 'date-fns'
import { MapPin, Calendar, Tag, DollarSign, Ticket, ChevronLeft, User, Edit2, Trash2, X } from 'lucide-react'
import { api } from '../api'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { useWebSocket } from '../hooks/useWebSocket'
import ReviewSection from '../components/ReviewSection'
import EventFormModal from '../components/EventFormModal'

export default function EventDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const { show } = useToast()

  const [event, setEvent] = useState(null)
  const [loading, setLoading] = useState(true)
  const [bookingCount, setBookingCount] = useState(1)
  const [booking, setBooking] = useState(false)
  const [error, setError] = useState('')
  const [editModalOpen, setEditModalOpen] = useState(false)

  const loadEvent = useCallback(() => {
    api.getEvent(id)
      .then(setEvent)
      .catch(() => navigate('/events'))
      .finally(() => setLoading(false))
  }, [id, navigate])

  useEffect(() => {
    loadEvent()
  }, [loadEvent])

  // Live ticket updates via WebSocket
  const handleWS = useCallback((msg) => {
    if (msg.type === 'TICKET_UPDATE') {
      setEvent(prev => prev ? { ...prev, available_tickets: msg.available_tickets } : prev)
    }
  }, [])
  useWebSocket(`/ws/events/${id}`, handleWS)

  const handleBook = async () => {
    if (!user) { navigate('/login'); return }
    setError('')
    setBooking(true)
    try {
      await api.createBooking({ event_id: id, ticket_count: bookingCount })
      show(`Booked ${bookingCount} ticket(s)! Check My Bookings.`, 'success')
      setEvent(prev => prev ? { ...prev, available_tickets: Math.max(0, prev.available_tickets - bookingCount) } : prev)
    } catch (err) {
      setError(err.message)
    } finally {
      setBooking(false)
    }
  }

  const handleCancelEvent = async () => {
    if (!confirm('Cancel this event? All attendees will be notified.')) return
    try {
      await api.cancelEvent(id)
      show('Event cancelled', 'success')
      loadEvent()
    } catch (err) {
      show(err.message, 'error')
    }
  }

  const handleDeleteEvent = async () => {
    if (!confirm('Are you sure you want to delete this event? This action cannot be undone.')) return
    try {
      await api.deleteEvent(id)
      show('Event deleted', 'success')
      navigate('/events')
    } catch (err) {
      show(err.message, 'error')
    }
  }

  if (loading) return <div className="spinner" style={{ marginTop: '4rem' }} />

  if (!event) return null

  const userRole = (user?.role || '').toLowerCase()
  const isOwner = user && (user.id === event.organizer_id || (event.organizer_email && user.email === event.organizer_email))
  const canManage = isOwner || userRole === 'admin'

  const soldOut = event.available_tickets === 0
  const canBook = user && event.status === 'Published' && !soldOut

  return (
    <div className="page">
      <div className="container">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '.75rem' }}>
          <button className="btn btn-ghost btn-sm" onClick={() => navigate(-1)}>
            <ChevronLeft size={15} /> Back
          </button>

          {canManage && (
            <div style={{ display: 'flex', gap: '.5rem' }}>
              <button
                className="btn btn-ghost btn-sm"
                onClick={() => setEditModalOpen(true)}
                disabled={event.status === 'Cancelled' || event.status === 'Completed'}
              >
                <Edit2 size={14} /> Edit Event
              </button>
              {event.status !== 'Cancelled' && event.status !== 'Completed' && (
                <button className="btn btn-ghost btn-sm" style={{ color: 'var(--danger)' }} onClick={handleCancelEvent}>
                  <X size={14} /> Cancel Event
                </button>
              )}
              <button className="btn btn-danger btn-sm" onClick={handleDeleteEvent}>
                <Trash2 size={14} /> Delete Event
              </button>
            </div>
          )}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '1.5rem', alignItems: 'start' }}>
          {/* Main */}
          <div>
            <div className="flex-gap" style={{ marginBottom: '.75rem', flexWrap: 'wrap' }}>
              <span className={`badge badge-${event.status.toLowerCase()}`}>{event.status}</span>
              {isOwner && (
                <span className="badge badge-published" style={{ background: 'var(--primary)', color: '#fff', fontWeight: 700 }}>
                  👑 Your Event
                </span>
              )}
              {event.category && <span className="badge badge-draft">{event.category}</span>}
              {event.tags?.map(t => (
                <span key={t} style={{ fontSize: '.72rem', color: 'var(--muted)' }}>#{t}</span>
              ))}
            </div>

            <h1 style={{ fontSize: 'clamp(1.5rem,4vw,2.2rem)', fontWeight: 800, marginBottom: '.85rem' }}>
              {event.title}
            </h1>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1.25rem', marginBottom: '1.5rem', color: 'var(--muted)', fontSize: '.9rem' }}>
              <span className="flex-gap">
                <Calendar size={15} />
                {format(new Date(event.event_date), "EEEE, MMMM d yyyy 'at' h:mm a")}
              </span>
              <span className="flex-gap">
                <MapPin size={15} /> {event.venue}
              </span>
              <span className="flex-gap" style={{ color: isOwner ? 'var(--primary)' : 'inherit', fontWeight: isOwner ? 600 : 400 }}>
                <User size={15} /> {isOwner ? 'Organized by you' : (event.organizer_email ? `Organized by ${event.organizer_email}` : 'Event Organizer')}
              </span>
              <span className="flex-gap">
                <DollarSign size={15} />
                {event.ticket_price === 0 ? 'Free' : `$${Number(event.ticket_price).toFixed(2)} per ticket`}
              </span>
            </div>

            <div className="card" style={{ marginBottom: '1.5rem' }}>
              <h2 style={{ fontWeight: 700, marginBottom: '.75rem', fontSize: '1rem' }}>About this event</h2>
              <p style={{ whiteSpace: 'pre-wrap', color: 'var(--muted)', lineHeight: 1.7 }}>{event.description}</p>
            </div>

            {/* Reviews */}
            <ReviewSection eventId={id} />
          </div>

          {/* Sidebar */}
          <div className="card" style={{ position: 'sticky', top: '80px' }}>
            <h3 style={{ fontWeight: 700, marginBottom: '1rem' }}>Book Tickets</h3>

            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '.5rem', fontSize: '.875rem' }}>
              <span className="text-muted">Available</span>
              <strong style={{ color: soldOut ? 'var(--danger)' : 'var(--success)' }}>
                {soldOut ? 'Sold out' : `${event.available_tickets} / ${event.total_tickets}`}
              </strong>
            </div>

            <div style={{ height: 4, background: 'var(--border)', borderRadius: 4, marginBottom: '1rem' }}>
              <div style={{
                height: '100%',
                borderRadius: 4,
                background: soldOut ? 'var(--danger)' : 'var(--primary)',
                width: `${Math.round((event.available_tickets / event.total_tickets) * 100)}%`,
                transition: 'width .4s',
              }} />
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem', fontSize: '.875rem' }}>
              <span className="text-muted">Price</span>
              <strong>{event.ticket_price === 0 ? 'Free' : `$${Number(event.ticket_price).toFixed(2)}`}</strong>
            </div>

            {error && <div className="alert alert-error" style={{ marginBottom: '1rem' }}>{error}</div>}

            {canBook && (
              <div className="form-group" style={{ marginBottom: '1rem' }}>
                <label htmlFor="ticket-count">Number of tickets</label>
                <input
                  id="ticket-count"
                  type="number"
                  min={1}
                  max={Math.min(event.available_tickets, 10)}
                  className="form-control"
                  value={bookingCount}
                  onChange={e => setBookingCount(Number(e.target.value))}
                />
              </div>
            )}

            {canBook ? (
              <button className="btn btn-primary w-100" onClick={handleBook} disabled={booking}>
                <Ticket size={15} />
                {booking ? 'Booking…' : `Book ${bookingCount} ticket${bookingCount > 1 ? 's' : ''}`}
              </button>
            ) : (
              <div style={{ textAlign: 'center', color: 'var(--muted)', fontSize: '.875rem' }}>
                {!user && (
                  <button className="btn btn-primary w-100" onClick={() => navigate('/login')}>
                    Sign in to book
                  </button>
                )}
                {user && isOwner && (
                  <div style={{ background: 'var(--bg-secondary)', padding: '.75rem', borderRadius: 'var(--radius)', border: '1px solid var(--border)' }}>
                    👑 <strong>You are the organizer</strong>
                    <div className="text-sm text-muted" style={{ marginTop: '.3rem' }}>Use the management buttons above to update this event.</div>
                  </div>
                )}
                {user && soldOut && (
                  <span style={{ color: 'var(--danger)', fontWeight: 600 }}>This event is sold out</span>
                )}
                {user && event.status !== 'Published' && (
                  <span>Booking not available (Event is {event.status})</span>
                )}
              </div>
            )}

            <div style={{ borderTop: '1px solid var(--border)', marginTop: '1rem', paddingTop: '1rem', fontSize: '.8rem', color: 'var(--muted)' }}>
              <div className="live-pill" style={{ marginBottom: '.5rem' }}>
                <span className="live-dot" /> Ticket count updates in real-time
              </div>
              Created {format(new Date(event.created_at), 'MMM d, yyyy')}
            </div>
          </div>
        </div>
      </div>

      {editModalOpen && (
        <EventFormModal
          event={event}
          onClose={() => setEditModalOpen(false)}
          onSaved={() => { setEditModalOpen(false); loadEvent() }}
        />
      )}
    </div>
  )
}
