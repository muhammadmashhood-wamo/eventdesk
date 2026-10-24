import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useToast } from '../context/ToastContext'

export default function RegisterPage() {
  const { show } = useToast()
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', password: '', name: '', role: 'attendee' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await api.register({
        email: form.email,
        password: form.password,
        name: form.name.trim() || undefined,
        role: form.role,
      })
      show('Account created! Please sign in.', 'success')
      navigate('/login')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex-center" style={{ minHeight: '80vh' }}>
      <div className="card" style={{ width: '100%', maxWidth: 420 }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 800, marginBottom: '.25rem' }}>Create account</h1>
        <p className="text-muted text-sm" style={{ marginBottom: '1.5rem' }}>
          Already have an account? <Link to="/login">Sign in</Link>
        </p>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="reg-name">Name (optional)</label>
            <input
              id="reg-name"
              type="text"
              className="form-control"
              placeholder="Your name"
              value={form.name}
              onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
            />
          </div>

          <div className="form-group">
            <label htmlFor="reg-email">Email</label>
            <input
              id="reg-email"
              type="email"
              className="form-control"
              placeholder="you@example.com"
              value={form.email}
              onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="reg-password">Password</label>
            <input
              id="reg-password"
              type="password"
              className="form-control"
              placeholder="••••••••"
              value={form.password}
              onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="reg-role">I want to</label>
            <select
              id="reg-role"
              className="form-control"
              value={form.role}
              onChange={e => setForm(f => ({ ...f, role: e.target.value }))}
            >
              <option value="attendee">Attend events</option>
              <option value="organizer">Organize events</option>
            </select>
          </div>

          <button type="submit" className="btn btn-primary w-100" disabled={loading}>
            {loading ? 'Creating…' : 'Create account'}
          </button>
        </form>
      </div>
    </div>
  )
}
