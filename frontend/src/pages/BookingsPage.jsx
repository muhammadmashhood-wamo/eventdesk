import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { format } from 'date-fns'
import { Ticket, X } from 'lucide-react'
import { api } from '../api'
import { useToast } from '../context/ToastContext'

export default function BookingsPage() {
  const navigate = useNavigate()
  const { show } = useToast()
  const [bookings, setBookings] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(0)
  const LIMIT = 10

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const d = await api.listBookings({ skip: page * LIMIT, limit: LIMIT })
      setBookings(d.items)
      setTotal(d.total)
    } catch {}
    setLoading(false)
  }, [page])

  useEffect(() => { load() }, [load])

  const handleCancel = async (id) => {
    if (!confirm('Cancel this booking?')) return
    try {
      await api.cancelBooking(id)
      show('Booking cancelled', 'success')
      load()
    } catch (err) {
      show(err.message, 'error')
    }
  }

  const totalPages = Math.ceil(total / LIMIT)

  return (
    <div className="page">
      <div className="container">
        <div className="section-header">
          <h1 className="section-title">My Bookings</h1>
          <span className="text-muted text-sm">{total} total</span>
        </div>

        {loading ? (
          <div className="spinner" />
        ) : bookings.length === 0 ? (
          <div className="empty-state">
            <Ticket size={40} color="var(--muted)" />
            <h3>No bookings yet</h3>
            <p>Browse events and book your first ticket</p>
            <button className="btn btn-primary" style={{ marginTop: '1rem' }} onClick={() => navigate('/events')}>
              Browse Events
            </button>
          </div>
        ) : (
          <>
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Event</th>
                      <th>Date</th>
                      <th>Tickets</th>
                      <th>Status</th>
                      <th>Booked</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {bookings.map(b => (
                      <tr key={b.id}>
                        <td>
                          <button
                            className="btn btn-ghost btn-sm"
                            onClick={() => navigate(`/events/${b.event_id}`)}
                            style={{ padding: 0, border: 'none', fontWeight: 600, color: 'var(--text)' }}
                          >
                            {b.event?.title ?? '—'}
                          </button>
                          <div className="text-muted text-sm">{b.event?.venue}</div>
                        </td>
                        <td className="text-muted text-sm">
                          {b.event?.event_date ? format(new Date(b.event.event_date), 'MMM d, yyyy') : '—'}
                        </td>
                        <td>{b.ticket_count}</td>
                        <td>
                          <span className={`badge ${b.status === 'Confirmed' ? 'badge-active' : 'badge-cancelled'}`}>
                            {b.status}
                          </span>
                        </td>
                        <td className="text-muted text-sm">
                          {format(new Date(b.created_at), 'MMM d, yyyy')}
                        </td>
                        <td>
                          {b.status === 'Confirmed' && (
                            <button className="btn btn-danger btn-sm" onClick={() => handleCancel(b.id)}>
                              <X size={13} /> Cancel
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {totalPages > 1 && (
              <div className="pagination">
                <button className="btn btn-ghost btn-sm" onClick={() => setPage(p => p - 1)} disabled={page === 0}>
                  ← Prev
                </button>
                <span className="text-muted text-sm">Page {page + 1} of {totalPages}</span>
                <button className="btn btn-ghost btn-sm" onClick={() => setPage(p => p + 1)} disabled={page + 1 >= totalPages}>
                  Next →
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
