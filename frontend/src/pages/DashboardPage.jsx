import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { format } from 'date-fns'
import { Plus, Edit2, X, Trash2, User, Users } from 'lucide-react'
import { api } from '../api'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import EventFormModal from '../components/EventFormModal'
import EventBookingsModal from '../components/EventBookingsModal'

export default function DashboardPage() {
  const { user } = useAuth()
  const { show } = useToast()
  const navigate = useNavigate()
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [editEvent, setEditEvent] = useState(null)
  const [bookingsEvent, setBookingsEvent] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const q = user?.role === 'organizer' ? { organizer_id: user.id, limit: 100 } : { limit: 100 }
      const d = await api.listEvents(q)
      setEvents(d.items || [])
    } catch {
      setEvents([])
    }
    setLoading(false)
  }, [user])

  useEffect(() => { load() }, [load])

  const handleCancel = async (id) => {
    if (!confirm('Cancel this event? All attendees will be notified.')) return
    try {
      await api.cancelEvent(id)
      show('Event cancelled', 'success')
      load()
    } catch (err) {
      show(err.message, 'error')
    }
  }

  const handleDelete = async (id, title) => {
    if (!confirm(`Delete event "${title}"? This cannot be undone.`)) return
    try {
      await api.deleteEvent(id)
      show('Event deleted', 'success')
      load()
    } catch (err) {
      show(err.message, 'error')
    }
  }

  const published = events.filter(e => e.status === 'Published').length
  const totalTicketsSold = events.reduce((s, e) => s + (e.total_tickets - e.available_tickets), 0)

  return (
    <div className="page">
      <div className="container">
        <div className="section-header">
          <h1 className="section-title">
            {user.role === 'admin' ? 'Admin Dashboard' : 'My Events'}
          </h1>
          <button className="btn btn-primary" onClick={() => { setEditEvent(null); setModalOpen(true) }}>
            <Plus size={16} /> New Event
          </button>
        </div>

        {/* Stats */}
        <div className="stats-grid">
          <div className="stat-card">
            <span className="stat-label">Total Events</span>
            <span className="stat-value">{events.length}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Published</span>
            <span className="stat-value" style={{ color: 'var(--primary)' }}>{published}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Tickets Sold</span>
            <span className="stat-value" style={{ color: 'var(--success)' }}>{totalTicketsSold}</span>
          </div>
        </div>

        {/* Events table */}
        {loading ? (
          <div className="spinner" />
        ) : events.length === 0 ? (
          <div className="empty-state">
            <h3>No events yet</h3>
            <p>Create your first event to get started</p>
          </div>
        ) : (
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Title</th>
                    {user?.role === 'admin' && <th>Organizer</th>}
                    <th>Date</th>
                    <th>Status</th>
                    <th>Tickets</th>
                    <th>Sold</th>
                    <th>Price</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {events.map(ev => (
                    <tr key={ev.id}>
                      <td>
                        <button
                          className="btn btn-ghost btn-sm"
                          onClick={() => navigate(`/events/${ev.id}`)}
                          style={{ padding: 0, border: 'none', fontWeight: 600, color: 'var(--text)' }}
                        >
                          {ev.title}
                        </button>
                        {ev.category && <div className="text-muted text-sm">{ev.category}</div>}
                      </td>
                      {user?.role === 'admin' && (
                        <td className="text-muted text-sm">{ev.organizer_email || '—'}</td>
                      )}
                      <td className="text-muted text-sm">
                        {format(new Date(ev.event_date), 'MMM d, yyyy')}
                      </td>
                      <td>
                        <span className={`badge badge-${ev.status.toLowerCase()}`}>{ev.status}</span>
                      </td>
                      <td>{ev.total_tickets}</td>
                      <td>
                        <span style={{ color: 'var(--success)' }}>
                          {ev.total_tickets - ev.available_tickets}
                        </span>
                      </td>
                      <td>${Number(ev.ticket_price).toFixed(2)}</td>
                      <td>
                        <div style={{ display: 'flex', gap: '.4rem' }}>
                          <button
                            className="btn btn-ghost btn-sm"
                            title="View Bookings"
                            onClick={() => setBookingsEvent(ev)}
                          >
                            <Users size={13} />
                          </button>
                          <button
                            className="btn btn-ghost btn-sm"
                            title="Edit Event"
                            onClick={() => { setEditEvent(ev); setModalOpen(true) }}
                            disabled={ev.status === 'Cancelled' || ev.status === 'Completed'}
                          >
                            <Edit2 size={13} />
                          </button>
                          {ev.status !== 'Cancelled' && ev.status !== 'Completed' && (
                            <button
                              className="btn btn-danger btn-sm"
                              title="Cancel Event"
                              onClick={() => handleCancel(ev.id)}
                            >
                              <X size={13} />
                            </button>
                          )}
                          <button
                            className="btn btn-ghost btn-sm"
                            style={{ color: 'var(--danger)' }}
                            title="Delete Event"
                            onClick={() => handleDelete(ev.id, ev.title)}
                          >
                            <Trash2 size={13} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {modalOpen && (
        <EventFormModal
          event={editEvent}
          onClose={() => setModalOpen(false)}
          onSaved={() => { setModalOpen(false); load() }}
        />
      )}

      {bookingsEvent && (
        <EventBookingsModal
          event={bookingsEvent}
          onClose={() => setBookingsEvent(null)}
          onBookingCancelled={load}
        />
      )}
    </div>
  )
}
