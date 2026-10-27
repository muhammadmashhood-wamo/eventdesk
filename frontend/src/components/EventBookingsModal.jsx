import { useState, useEffect, useCallback } from 'react'
import { format } from 'date-fns'
import { X, Ban } from 'lucide-react'
import { api } from '../api'
import { useToast } from '../context/ToastContext'

export default function EventBookingsModal({ event, onClose, onBookingCancelled }) {
  const { show } = useToast()
  const [bookings, setBookings] = useState([])
  const [loading, setLoading] = useState(true)
  const [cancellingId, setCancellingId] = useState(null)

  const loadBookings = useCallback(async () => {
    if (!event?.id) return
    setLoading(true)
    try {
      const res = await api.listEventBookings(event.id, { limit: 100 })
      setBookings(res.items || [])
    } catch (err) {
      show(err.message || 'Failed to load bookings', 'error')
      setBookings([])
    } finally {
      setLoading(false)
    }
  }, [event?.id, show])

  useEffect(() => {
    loadBookings()
  }, [loadBookings])

  const handleCancelBooking = async (booking) => {
    const attendee = booking.user_name || booking.user_email || 'attendee'
    if (!confirm(`Cancel booking for ${attendee} (${booking.ticket_count} ticket${booking.ticket_count > 1 ? 's' : ''})?`)) {
      return
    }

    setCancellingId(booking.id)
    try {
      await api.cancelBooking(booking.id)
      show(`Cancelled booking for ${attendee}`, 'success')
      await loadBookings()
      if (onBookingCancelled) {
        onBookingCancelled()
      }
    } catch (err) {
      show(err.message || 'Failed to cancel booking', 'error')
    } finally {
      setCancellingId(null)
    }
  }

  const confirmedCount = bookings.filter((b) => b.status === 'Confirmed').length
  const totalTickets = bookings
    .filter((b) => b.status === 'Confirmed')
    .reduce((sum, b) => sum + b.ticket_count, 0)

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: 760, width: '95%' }}
      >
        <div className="modal-header">
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Event Bookings</h2>
            <div className="text-sm text-muted">{event?.title}</div>
          </div>
          <button className="btn btn-ghost btn-sm" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <div style={{ display: 'flex', gap: '1rem', margin: '1rem 0' }}>
          <div className="stat-card" style={{ flex: 1, padding: '.75rem 1rem' }}>
            <span className="stat-label">Active Bookings</span>
            <span className="stat-value" style={{ fontSize: '1.4rem' }}>{confirmedCount}</span>
          </div>
          <div className="stat-card" style={{ flex: 1, padding: '.75rem 1rem' }}>
            <span className="stat-label">Tickets Reserved</span>
            <span className="stat-value" style={{ fontSize: '1.4rem', color: 'var(--primary)' }}>
              {totalTickets}
            </span>
          </div>
          <div className="stat-card" style={{ flex: 1, padding: '.75rem 1rem' }}>
            <span className="stat-label">Available Tickets</span>
            <span className="stat-value" style={{ fontSize: '1.4rem', color: 'var(--success)' }}>
              {event?.available_tickets ?? '—'}
            </span>
          </div>
        </div>

        {loading ? (
          <div className="spinner" style={{ margin: '2rem auto' }} />
        ) : bookings.length === 0 ? (
          <div className="empty-state" style={{ padding: '2rem 1rem' }}>
            <h3>No bookings yet</h3>
            <p>No attendees have booked tickets for this event yet.</p>
          </div>
        ) : (
          <div className="table-wrap" style={{ maxHeight: 360, overflowY: 'auto' }}>
            <table>
              <thead>
                <tr>
                  <th>Attendee</th>
                  <th>Tickets</th>
                  <th>Booked On</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {bookings.map((b) => (
                  <tr key={b.id}>
                    <td>
                      <div style={{ fontWeight: 600 }}>{b.user_name || 'Attendee'}</div>
                      <div className="text-sm text-muted">{b.user_email || b.user_id}</div>
                    </td>
                    <td>{b.ticket_count}</td>
                    <td className="text-sm text-muted">
                      {b.created_at ? format(new Date(b.created_at), 'MMM d, yyyy h:mm a') : '—'}
                    </td>
                    <td>
                      <span className={`badge badge-${(b.status || '').toLowerCase()}`}>
                        {b.status}
                      </span>
                    </td>
                    <td>
                      {b.status === 'Confirmed' ? (
                        <button
                          className="btn btn-ghost btn-sm"
                          style={{ color: 'var(--danger)' }}
                          onClick={() => handleCancelBooking(b)}
                          disabled={cancellingId === b.id}
                        >
                          <Ban size={14} />
                          {cancellingId === b.id ? 'Cancelling…' : 'Cancel Booking'}
                        </button>
                      ) : (
                        <span className="text-sm text-muted">Cancelled</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1.25rem' }}>
          <button className="btn btn-ghost" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
