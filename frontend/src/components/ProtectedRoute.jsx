import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function ProtectedRoute({ children, roles = [] }) {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    return <div className="page-loading">Loading session…</div>
  }

  if (!user) {
    return <Navigate to={`/login?redirect=${encodeURIComponent(location.pathname + location.search)}`} replace />
  }

  const userRole = String(user.role || '').toLowerCase()
  const allowedRoles = roles.map((role) => String(role).toLowerCase())

  if (roles.length && !allowedRoles.includes(userRole)) {
    return <Navigate to="/403" replace />
  }

  return children
}
