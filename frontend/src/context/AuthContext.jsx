import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { api } from '../api'

const AuthContext = createContext(null)

function normalizeRole(value) {
  return typeof value === 'string' ? value.toLowerCase() : ''
}

function formatUser(user) {
  if (!user) return null
  const role = normalizeRole(user.role)
  return {
    ...user,
    role,
    isAdmin: role === 'admin',
    isOrganizer: role === 'organizer',
    isAttendee: role === 'attendee',
  }
}

export function AuthProvider({ children }) {
  const queryClient = useQueryClient()
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  const clearSession = useCallback(() => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    setUser(null)
    queryClient.clear()
  }, [queryClient])

  const loadUser = useCallback(async () => {
    const accessToken = localStorage.getItem('access_token')
    if (!accessToken) {
      setUser(null)
      setLoading(false)
      return
    }

    try {
      const data = await api.me()
      setUser(formatUser(data))
    } catch {
      clearSession()
    } finally {
      setLoading(false)
    }
  }, [clearSession])

  useEffect(() => {
    loadUser()
  }, [loadUser])

  const login = useCallback(async (email, password) => {
    const data = await api.login({ email, password })
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    const me = await api.me()
    const nextUser = formatUser(me)
    setUser(nextUser)
    return nextUser
  }, [])

  const logout = useCallback(async () => {
    try {
      await api.logout()
    } catch {
      // ignore logout API failures and still clear local state
    }
    clearSession()
    return true
  }, [clearSession])

  const refreshSession = useCallback(async () => {
    const refreshToken = localStorage.getItem('refresh_token')
    if (!refreshToken) {
      clearSession()
      return false
    }

    try {
      const data = await api.refresh({ refresh_token: refreshToken })
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      const me = await api.me()
      setUser(formatUser(me))
      return true
    } catch {
      clearSession()
      return false
    }
  }, [clearSession])

  return (
    <AuthContext.Provider value={{
      user,
      loading,
      login,
      logout,
      reload: loadUser,
      refreshSession,
      isAdmin: user?.isAdmin ?? false,
      isOrganizer: user?.isOrganizer ?? false,
      isAttendee: user?.isAttendee ?? false,
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
