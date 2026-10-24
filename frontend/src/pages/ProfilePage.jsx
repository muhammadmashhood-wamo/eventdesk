import { useState, useEffect } from 'react'
import { format } from 'date-fns'
import { User, Shield, KeyRound, Mail, CheckCircle2 } from 'lucide-react'
import { api } from '../api'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'

export default function ProfilePage() {
  const { user, reload } = useAuth()
  const { show } = useToast()

  const [email, setEmail] = useState('')
  const [savingEmail, setSavingEmail] = useState(false)

  const [passwords, setPasswords] = useState({ current_password: '', new_password: '', confirm_password: '' })
  const [changingPwd, setChangingPwd] = useState(false)

  useEffect(() => {
    if (user?.email) setEmail(user.email)
  }, [user])

  const handleUpdateEmail = async (e) => {
    e.preventDefault()
    if (!email || email === user?.email) {
      show('No changes to email.', 'info')
      return
    }
    setSavingEmail(true)
    try {
      await api.updateProfile({ email })
      await reload()
      show('Email updated successfully!', 'success')
    } catch (err) {
      show(err.message, 'error')
    } finally {
      setSavingEmail(false)
    }
  }

  const handlePassword = async (e) => {
    e.preventDefault()
    if (passwords.new_password !== passwords.confirm_password) {
      show('New passwords do not match.', 'error')
      return
    }
    setChangingPwd(true)
    try {
      await api.changePassword({
        current_password: passwords.current_password,
        new_password: passwords.new_password,
      })
      show('Password changed successfully!', 'success')
      setPasswords({ current_password: '', new_password: '', confirm_password: '' })
    } catch (err) {
      show(err.message, 'error')
    } finally {
      setChangingPwd(false)
    }
  }

  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 600 }}>
        <div className="section-header" style={{ marginBottom: '1.5rem' }}>
          <h1 className="section-title">
            <User size={24} style={{ verticalAlign: 'middle', marginRight: '.5rem', color: 'var(--primary)' }} />
            My Profile
          </h1>
          <span className="badge badge-published" style={{ textTransform: 'capitalize' }}>
            {user?.role} Account
          </span>
        </div>

        {/* Profile Details & Update Email */}
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <h2 style={{ fontWeight: 700, marginBottom: '1.25rem', fontSize: '1.05rem', display: 'flex', alignItems: 'center', gap: '.5rem' }}>
            <Mail size={18} color="var(--primary)" /> Profile Information
          </h2>

          <form onSubmit={handleUpdateEmail}>
            <div className="form-group">
              <label htmlFor="profile-email">Email Address</label>
              <input
                id="profile-email"
                type="email"
                className="form-control"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label>Assigned Role</label>
                <div style={{ padding: '.55rem .75rem', background: 'var(--bg-secondary)', borderRadius: 'var(--radius)', border: '1px solid var(--border)', fontWeight: 600, textTransform: 'capitalize' }}>
                  <Shield size={14} style={{ display: 'inline', marginRight: '.35rem', verticalAlign: 'middle' }} />
                  {user?.role}
                </div>
              </div>

              <div className="form-group" style={{ marginBottom: 0 }}>
                <label>Account Status</label>
                <div style={{ padding: '.55rem .75rem', background: 'var(--bg-secondary)', borderRadius: 'var(--radius)', border: '1px solid var(--border)', fontWeight: 600 }}>
                  <CheckCircle2 size={14} style={{ display: 'inline', marginRight: '.35rem', verticalAlign: 'middle', color: 'var(--success)' }} />
                  {user?.is_active ? 'Active' : 'Inactive'}
                </div>
              </div>
            </div>

            {user?.created_at && (
              <p className="text-muted text-sm" style={{ marginBottom: '1.25rem' }}>
                Member since {format(new Date(user.created_at), 'MMMM d, yyyy')}
              </p>
            )}

            <button type="submit" className="btn btn-primary btn-sm" disabled={savingEmail || email === user?.email}>
              {savingEmail ? 'Saving changes…' : 'Update Email'}
            </button>
          </form>
        </div>

        {/* Change Password Card */}
        <div className="card">
          <h2 style={{ fontWeight: 700, marginBottom: '1.25rem', fontSize: '1.05rem', display: 'flex', alignItems: 'center', gap: '.5rem' }}>
            <KeyRound size={18} color="var(--primary)" /> Change Password
          </h2>

          <form onSubmit={handlePassword}>
            <div className="form-group">
              <label htmlFor="current-pwd">Current Password</label>
              <input
                id="current-pwd"
                type="password"
                className="form-control"
                placeholder="••••••••"
                value={passwords.current_password}
                onChange={e => setPasswords(p => ({ ...p, current_password: e.target.value }))}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="new-pwd">New Password</label>
              <input
                id="new-pwd"
                type="password"
                className="form-control"
                placeholder="At least 8 chars, 1 uppercase, 1 lowercase, 1 digit, 1 special char"
                value={passwords.new_password}
                onChange={e => setPasswords(p => ({ ...p, new_password: e.target.value }))}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="confirm-pwd">Confirm New Password</label>
              <input
                id="confirm-pwd"
                type="password"
                className="form-control"
                placeholder="Repeat new password"
                value={passwords.confirm_password}
                onChange={e => setPasswords(p => ({ ...p, confirm_password: e.target.value }))}
                required
              />
            </div>

            <button type="submit" className="btn btn-primary btn-sm" disabled={changingPwd}>
              {changingPwd ? 'Updating password…' : 'Change Password'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
