import { useState, useEffect, useCallback } from 'react'
import { format } from 'date-fns'
import { Users, Shield, Check, X } from 'lucide-react'
import { api } from '../api'
import { useToast } from '../context/ToastContext'

export default function AdminUsersPage() {
  const { show } = useToast()
  const [users, setUsers] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(0)
  const LIMIT = 15

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const d = await api.listUsers({ skip: page * LIMIT, limit: LIMIT })
      setUsers(d.items)
      setTotal(d.total)
    } catch {}
    setLoading(false)
  }, [page])

  useEffect(() => { load() }, [load])

  const updateUser = async (id, payload) => {
    try {
      await api.updateUser(id, payload)
      show('User updated', 'success')
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
          <h1 className="section-title"><Users size={22} style={{ verticalAlign: 'middle', marginRight: '.4rem' }} /> User Management</h1>
          <span className="text-muted text-sm">{total} users</span>
        </div>

        {loading ? <div className="spinner" /> : (
          <>
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>User</th>
                      <th>Role</th>
                      <th>Status</th>
                      <th>Joined</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map(u => (
                      <tr key={u.id}>
                        <td>
                          <div style={{ fontWeight: 600 }}>{u.name || '—'}</div>
                          <div className="text-muted text-sm">{u.email}</div>
                        </td>
                        <td>
                          <select
                            className="form-control"
                            style={{ padding: '.3rem .6rem', width: 'auto', fontSize: '.8rem' }}
                            value={(u.role || '').toLowerCase()}
                            onChange={e => updateUser(u.id, { role: e.target.value })}
                          >
                            <option value="attendee">Attendee</option>
                            <option value="organizer">Organizer</option>
                            <option value="admin">Admin</option>
                          </select>
                        </td>
                        <td>
                          <span className={`badge ${u.is_active ? 'badge-active' : 'badge-inactive'}`}>
                            {u.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        <td className="text-muted text-sm">
                          {format(new Date(u.created_at), 'MMM d, yyyy')}
                        </td>
                        <td>
                          <button
                            className={`btn btn-sm ${u.is_active ? 'btn-danger' : 'btn-primary'}`}
                            onClick={() => updateUser(u.id, { is_active: !u.is_active })}
                          >
                            {u.is_active ? <><X size={13} /> Deactivate</> : <><Check size={13} /> Activate</>}
                          </button>
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
