import { useState, useEffect } from 'react'
import { X } from 'lucide-react'
import { api } from '../api'
import { useToast } from '../context/ToastContext'

const EMPTY = {
  title: '', description: '', venue: '', event_date: '',
  ticket_price: '', total_tickets: '', category: '', tags: '', status: 'Draft',
}

export default function EventFormModal({ event, onClose, onSaved }) {
  const { show } = useToast()
  const [form, setForm] = useState(EMPTY)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (event) {
      // Format datetime-local input
      const dt = event.event_date
        ? new Date(event.event_date).toISOString().slice(0, 16)
        : ''
      setForm({
        title: event.title || '',
        description: event.description || '',
        venue: event.venue || '',
        event_date: dt,
        ticket_price: event.ticket_price ?? '',
        total_tickets: event.total_tickets ?? '',
        category: event.category || '',
        tags: (event.tags || []).join(', '),
        status: event.status || 'Draft',
      })
    } else {
      setForm(EMPTY)
    }
  }, [event])

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    const payload = {
      title: form.title,
      description: form.description,
      venue: form.venue,
      event_date: new Date(form.event_date).toISOString(),
      ticket_price: parseFloat(form.ticket_price),
      total_tickets: parseInt(form.total_tickets),
      category: form.category || null,
      tags: form.tags ? form.tags.split(',').map(t => t.trim()).filter(Boolean) : [],
      status: form.status,
    }

    try {
      if (event) {
        await api.updateEvent(event.id, payload)
        show('Event updated!', 'success')
      } else {
        await api.createEvent(payload)
        show('Event created!', 'success')
      }
      onSaved()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <h2 className="modal-title">{event ? 'Edit Event' : 'Create Event'}</h2>
          <button className="modal-close" onClick={onClose}><X size={18} /></button>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Title *</label>
            <input className="form-control" value={form.title} onChange={e => set('title', e.target.value)} required />
          </div>

          <div className="form-group">
            <label>Description *</label>
            <textarea className="form-control" value={form.description} onChange={e => set('description', e.target.value)} required />
          </div>

          <div className="grid-2">
            <div className="form-group">
              <label>Venue *</label>
              <input className="form-control" value={form.venue} onChange={e => set('venue', e.target.value)} required />
            </div>
            <div className="form-group">
              <label>Date & Time *</label>
              <input type="datetime-local" className="form-control" value={form.event_date} onChange={e => set('event_date', e.target.value)} required />
            </div>
          </div>

          <div className="grid-2">
            <div className="form-group">
              <label>Price ($) *</label>
              <input type="number" min="0" step="0.01" className="form-control" value={form.ticket_price} onChange={e => set('ticket_price', e.target.value)} required />
            </div>
            <div className="form-group">
              <label>Total Tickets *</label>
              <input type="number" min="1" className="form-control" value={form.total_tickets} onChange={e => set('total_tickets', e.target.value)} required />
            </div>
          </div>

          <div className="grid-2">
            <div className="form-group">
              <label>Category</label>
              <select className="form-control" value={form.category} onChange={e => set('category', e.target.value)}>
                <option value="">None</option>
                <option value="Concert">Concert</option>
                <option value="Workshop">Workshop</option>
                <option value="Meetup">Meetup</option>
                <option value="Conference">Conference</option>
                <option value="Sports">Sports</option>
                <option value="Other">Other</option>
              </select>
            </div>
            <div className="form-group">
              <label>Status</label>
              <select className="form-control" value={form.status} onChange={e => set('status', e.target.value)}>
                <option value="Draft">Draft</option>
                <option value="Published">Published</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label>Tags (comma-separated)</label>
            <input className="form-control" placeholder="music, outdoor, free" value={form.tags} onChange={e => set('tags', e.target.value)} />
          </div>

          <div style={{ display: 'flex', gap: '.75rem', justifyContent: 'flex-end' }}>
            <button type="button" className="btn btn-ghost" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Saving…' : event ? 'Save Changes' : 'Create Event'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
