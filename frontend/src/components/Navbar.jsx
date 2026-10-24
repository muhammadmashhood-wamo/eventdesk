import { NavLink, useNavigate } from 'react-router-dom'
import { Bell, LogOut, LayoutDashboard, Ticket, Calendar, Users, ClipboardList, User } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useNotifCount } from '../hooks/useNotifCount'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const unread = useNotifCount()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <NavLink to="/" className="navbar-brand">
          Event<span>Desk</span>
        </NavLink>

        <div className="navbar-links">
          <NavLink to="/events" className={({ isActive }) => 'navbar-link' + (isActive ? ' active' : '')}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '.35rem' }}>
              <Calendar size={15} /> Events
            </span>
          </NavLink>

          {user && (
            <>
              <NavLink to="/bookings" className={({ isActive }) => 'navbar-link' + (isActive ? ' active' : '')}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '.35rem' }}>
                  <Ticket size={15} /> My Bookings
                </span>
              </NavLink>

              <NavLink to="/notifications" className={({ isActive }) => 'navbar-link' + (isActive ? ' active' : '')}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '.35rem' }}>
                  <Bell size={15} /> Notifications
                  {unread > 0 && <span className="notif-dot" />}
                </span>
              </NavLink>

              {(user.role === 'organizer' || user.role === 'admin') && (
                <NavLink to="/dashboard" className={({ isActive }) => 'navbar-link' + (isActive ? ' active' : '')}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '.35rem' }}>
                    <LayoutDashboard size={15} /> Dashboard
                  </span>
                </NavLink>
              )}

              {user.role === 'admin' && (
                <>
                  <NavLink to="/admin/users" className={({ isActive }) => 'navbar-link' + (isActive ? ' active' : '')}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '.35rem' }}>
                      <Users size={15} /> Users
                    </span>
                  </NavLink>
                  <NavLink to="/admin/audit-logs" className={({ isActive }) => 'navbar-link' + (isActive ? ' active' : '')}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '.35rem' }}>
                      <ClipboardList size={15} /> Audit
                    </span>
                  </NavLink>
                </>
              )}

              <NavLink to="/profile" className={({ isActive }) => 'navbar-link' + (isActive ? ' active' : '')}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '.35rem' }}>
                  <User size={15} /> Profile
                </span>
              </NavLink>

              <div style={{ display: 'flex', alignItems: 'center', gap: '.5rem', marginLeft: '.5rem', paddingLeft: '.5rem', borderLeft: '1px solid var(--border)' }}>
                <span className={`badge ${user.role === 'admin' ? 'badge-cancelled' : user.role === 'organizer' ? 'badge-published' : 'badge-completed'}`} style={{ textTransform: 'capitalize', fontSize: '.75rem' }}>
                  {user.role}
                </span>
                <span className="text-muted text-sm" style={{ maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={user.email}>
                  {user.email}
                </span>
              </div>

              <button className="btn btn-ghost btn-sm" onClick={handleLogout} title="Sign out">
                <LogOut size={14} /> Logout
              </button>
            </>
          )}

          {!user && (
            <>
              <NavLink to="/login" className="navbar-link">Login</NavLink>
              <NavLink to="/register">
                <button className="btn btn-primary btn-sm">Sign Up</button>
              </NavLink>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}
