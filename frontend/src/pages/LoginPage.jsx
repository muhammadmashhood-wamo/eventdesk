import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'

export default function LoginPage() {
  const { login } = useAuth()
  const { show } = useToast()
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const u = await login(form.email, form.password)
      show('Welcome back!', 'success')
      if (u.role === 'admin' || u.role === 'organizer') navigate('/dashboard')
      else navigate('/events')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex-center" style={{ minHeight: '80vh' }}>
      <div className="card" style={{ width: '100%', maxWidth: 420 }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 800, marginBottom: '.25rem' }}>Sign in</h1>
        <p className="text-muted text-sm" style={{ marginBottom: '1.5rem' }}>
          Don't have an account? <Link to="/register">Sign up</Link>
        </p>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="login-email">Email</label>
            <input
              id="login-email"
              type="email"
              className="form-control"
              placeholder="you@example.com"
              value={form.email}
              onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="login-password">Password</label>
            <input
              id="login-password"
              type="password"
              className="form-control"
              placeholder="••••••••"
              value={form.password}
              onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
              required
            />
          </div>

          <button type="submit" className="btn btn-primary w-100" disabled={loading}>
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <div style={{ marginTop: '1.5rem', paddingTop: '1.25rem', borderTop: '1px solid var(--border)' }}>
          <p className="text-muted text-sm" style={{ marginBottom: '.6rem', textAlign: 'center' }}>
            Quick fill test accounts:
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '.5rem' }}>
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={() => setForm({ email: 'admin@eventdesk.com', password: 'Password123!' })}
            >
              Admin
            </button>
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={() => setForm({ email: 'organizer@eventdesk.com', password: 'Password123!' })}
            >
              Organizer
            </button>
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={() => setForm({ email: 'alice@eventdesk.com', password: 'Password123!' })}
            >
              Attendee
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
