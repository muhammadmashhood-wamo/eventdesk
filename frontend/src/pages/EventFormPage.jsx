import { useEffect, useMemo, useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'

const emptyForm = {
  title: '',
  description: '',
  category: '',
  venue: '',
  event_date: '',
  ticket_price: '',
  total_tickets: '',
  tags: '',
  status: 'Draft',
}

export default function EventFormPage() {
  const { id } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const { user } = useAuth()
  const { show } = useToast()
  const [form, setForm] = useState(emptyForm)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const editing = Boolean(id)

  const { data, isLoading, isError } = useQuery({
    queryKey: ['event-form', id],
    queryFn: () => api.getEvent(id),
    enabled: editing,
  })

  useEffect(() => {
    if (location.state?.event) {
      const next = location.state.event
      setForm({
        title: next.title || '',
        description: next.description || '',
        category: next.category || '',
        venue: next.venue || '',
        event_date: next.event_date ? new Date(next.event_date).toISOString().slice(0, 16) : '',
        ticket_price: next.ticket_price ?? '',
        total_tickets: next.total_tickets ?? '',
        tags: (next.tags || []).join(', '),
        status: next.status || 'Draft',
      })
      return
    }

    if (editing && data) {
      setForm({
        title: data.title || '',
        description: data.description || '',
        category: data.category || '',
        venue: data.venue || '',
        event_date: data.event_date ? new Date(data.event_date).toISOString().slice(0, 16) : '',
        ticket_price: data.ticket_price ?? '',
        total_tickets: data.total_tickets ?? '',
        tags: (data.tags || []).join(', '),
        status: data.status || 'Draft',
      })
    }
  }, [data, editing, location.state])

  const isOrganizer = user && (user.isOrganizer || user.isAdmin)

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setSaving(true)

    try {
      const payload = {
        title: form.title.trim(),
        description: form.description.trim(),
        category: form.category.trim() || null,
        venue: form.venue.trim(),
        event_date: new Date(form.event_date).toISOString(),
        ticket_price: Number(form.ticket_price),
        total_tickets: Number(form.total_tickets),
        tags: form.tags.split(',').map((item) => item.trim()).filter(Boolean),
        status: form.status,
      }

      if (!payload.title || !payload.description || !payload.venue || !payload.event_date) {
        throw new Error('Please complete all required fields.')
      }

      if (Number(payload.ticket_price) <= 0) {
        throw new Error('Ticket price must be greater than zero.')
      }

      if (Number(payload.total_tickets) <= 0) {
        throw new Error('Ticket count must be greater than zero.')
      }

      if (!editing) {
        const created = await api.createEvent(payload)
        show('Event created successfully.', 'success')
        navigate(`/events/${created.id}/edit`, { state: { event: created } })
        return
      }

      const updated = await api.updateEvent(id, payload)
      show('Event saved.', 'success')
      navigate(`/events/${updated.id}`)
    } catch (err) {
      setError(err.message)
      show(err.message || 'Unable to save event', 'error')
    } finally {
      setSaving(false)
    }
  }

  if (!isOrganizer) {
    return <div className="page-loading">Only organizers and admins can manage events.</div>
  }

  if (editing && isLoading) {
    return <div className="page-loading">Loading event…</div>
  }

  if (editing && isError) {
    return (
      <div className="page-shell">
        <div className="container narrow">
          <div className="empty-state">
            <h3>This draft cannot be reloaded</h3>
            <p>The backend refuses draft detail requests for non-published items. Create or reopen the event from the organizer flow.</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="page-shell">
      <div className="container narrow">
        <div className="panel">
          <div className="section-header">
            <h1>{editing ? 'Edit event' : 'Create event'}</h1>
          </div>

          {error && <div className="alert alert-error">{error}</div>}

          <form className="stack-form" onSubmit={handleSubmit}>
            <div className="field">
              <label htmlFor="event-form-title">Title</label>
              <input id="event-form-title" value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} maxLength={120} required />
            </div>

            <div className="field">
              <label htmlFor="event-form-description">Description</label>
              <textarea id="event-form-description" value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} maxLength={2048} required />
            </div>

            <div className="two-col">
              <div className="field">
                <label htmlFor="event-form-category">Category</label>
                <input id="event-form-category" value={form.category} onChange={(event) => setForm({ ...form, category: event.target.value })} maxLength={120} />
              </div>
              <div className="field">
                <label htmlFor="event-form-venue">Venue</label>
                <input id="event-form-venue" value={form.venue} onChange={(event) => setForm({ ...form, venue: event.target.value })} required />
              </div>
            </div>

            <div className="two-col">
              <div className="field">
                <label htmlFor="event-form-date">Event date</label>
                <input id="event-form-date" type="datetime-local" value={form.event_date} onChange={(event) => setForm({ ...form, event_date: event.target.value })} required />
              </div>
              <div className="field">
                <label htmlFor="event-form-status">Status</label>
                <select id="event-form-status" value={form.status} onChange={(event) => setForm({ ...form, status: event.target.value })}>
                  <option value="Draft">Draft</option>
                  <option value="Published">Published</option>
                </select>
              </div>
            </div>

            <div className="two-col">
              <div className="field">
                <label htmlFor="event-form-price">Ticket price</label>
                <input id="event-form-price" type="number" min="0.01" step="0.01" value={form.ticket_price} onChange={(event) => setForm({ ...form, ticket_price: event.target.value })} required />
              </div>
              <div className="field">
                <label htmlFor="event-form-tickets">Total tickets</label>
                <input id="event-form-tickets" type="number" min="1" step="1" value={form.total_tickets} onChange={(event) => setForm({ ...form, total_tickets: event.target.value })} required />
              </div>
            </div>

            <div className="field">
              <label htmlFor="event-form-tags">Tags</label>
              <input id="event-form-tags" value={form.tags} onChange={(event) => setForm({ ...form, tags: event.target.value })} placeholder="music, workshop, community" />
            </div>

            <div className="toolbar-row">
              <button className="btn btn-ghost" type="button" onClick={() => navigate(-1)}>Cancel</button>
              <button className="btn btn-primary" type="submit" disabled={saving}>
                {saving ? 'Saving…' : editing ? 'Save changes' : 'Create event'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
