import { useState, useEffect, useCallback } from 'react'
import { format } from 'date-fns'
import { ClipboardList, Search } from 'lucide-react'
import { api } from '../api'

const ACTION_COLORS = {
  EVENT_CREATED:         'var(--success)',
  EVENT_CANCELLED:       'var(--danger)',
  EVENT_DELETED:         'var(--danger)',
  BOOKING_CREATED:       'var(--primary)',
  BOOKING_CANCELLED:     'var(--danger)',
  BOOKING_DELETED:       'var(--danger)',
  USER_UPDATED_BY_ADMIN: 'var(--accent)',
  USER_DELETED_BY_ADMIN: 'var(--danger)',
}

export default function AuditLogsPage() {
  const [logs, setLogs] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(0)
  const [actionFilter, setActionFilter] = useState('')
  const LIMIT = 20

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const q = { skip: page * LIMIT, limit: LIMIT }
      if (actionFilter) q.action = actionFilter
      const d = await api.listAuditLogs(q)
      setLogs(d.items)
      setTotal(d.total)
    } catch {}
    setLoading(false)
  }, [page, actionFilter])

  useEffect(() => { load() }, [load])

  const totalPages = Math.ceil(total / LIMIT)

  return (
    <div className="page">
      <div className="container">
        <div className="section-header">
          <h1 className="section-title">
            <ClipboardList size={22} style={{ verticalAlign: 'middle', marginRight: '.4rem' }} />
            Audit Logs
          </h1>
          <span className="text-muted text-sm">{total} entries</span>
        </div>

        {/* Filter */}
        <div className="filter-bar">
          <select
            className="form-control"
            style={{ minWidth: 220 }}
            value={actionFilter}
            onChange={e => { setActionFilter(e.target.value); setPage(0) }}
          >
            <option value="">All actions</option>
            <option value="EVENT_CREATED">Event Created</option>
            <option value="EVENT_CANCELLED">Event Cancelled</option>
            <option value="EVENT_DELETED">Event Deleted</option>
            <option value="BOOKING_CREATED">Booking Created</option>
            <option value="BOOKING_CANCELLED">Booking Cancelled</option>
            <option value="BOOKING_DELETED">Booking Deleted</option>
            <option value="BOOKING_DELETED">Booking Deleted</option>
            <option value="USER_UPDATED_BY_ADMIN">User Updated by Admin</option>
            <option value="USER_DELETED_BY_ADMIN">User Deleted by Admin</option>
          </select>
        </div>

        {loading ? <div className="spinner" /> : (
          <>
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Action</th>
                      <th>Details</th>
                      <th>User ID</th>
                      <th>Timestamp</th>
                    </tr>
                  </thead>
                  <tbody>
                    {logs.length === 0 ? (
                      <tr>
                        <td colSpan={4} style={{ textAlign: 'center', color: 'var(--muted)', padding: '2rem' }}>
                          No logs found
                        </td>
                      </tr>
                    ) : logs.map(l => (
                      <tr key={l.id}>
                        <td>
                          <span style={{
                            fontWeight: 700,
                            fontSize: '.8rem',
                            color: ACTION_COLORS[l.action] || 'var(--text)',
                          }}>
                            {l.action}
                          </span>
                        </td>
                        <td style={{ maxWidth: 360, fontSize: '.8rem', color: 'var(--muted)' }}>
                          {l.details}
                        </td>
                        <td style={{ fontSize: '.75rem', color: 'var(--muted)', fontFamily: 'monospace' }}>
                          {l.user_id?.slice(0, 8)}…
                        </td>
                        <td className="text-muted text-sm">
                          {format(new Date(l.created_at), 'MMM d, yyyy HH:mm')}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {totalPages > 1 && (
              <div className="pagination">
                <button className="btn btn-ghost btn-sm" onClick={() => setPage(p => p - 1)} disabled={page === 0}>← Prev</button>
                <span className="text-muted text-sm">Page {page + 1} of {totalPages}</span>
                <button className="btn btn-ghost btn-sm" onClick={() => setPage(p => p + 1)} disabled={page + 1 >= totalPages}>Next →</button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
