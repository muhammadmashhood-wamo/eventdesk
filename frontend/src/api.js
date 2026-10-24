const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000/api/v1'
const AUTH_ROUTES = ['/auth/login', '/auth/refresh', '/auth/register']

let refreshPromise = null

function buildQuery(params = {}) {
  const searchParams = new URLSearchParams()

  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') {
      return
    }
    if (Array.isArray(value)) {
      value.forEach((item) => item !== undefined && item !== null && searchParams.append(key, String(item)))
      return
    }
    searchParams.append(key, String(value))
  })

  const queryString = searchParams.toString()
  return queryString ? `?${queryString}` : ''
}

function getAccessToken() {
  return localStorage.getItem('access_token') || ''
}

function getRefreshToken() {
  return localStorage.getItem('refresh_token') || ''
}

async function safeJson(response) {
  try {
    return await response.json()
  } catch {
    return null
  }
}

function normalizeErrorPayload(detail) {
  if (Array.isArray(detail)) {
    return detail
      .map((entry) => {
        const loc = Array.isArray(entry?.loc) ? entry.loc.filter((part) => part !== 'body').join('.') : ''
        const msg = entry?.msg || 'Invalid value'
        return loc ? `${loc}: ${msg.replace(/^Value error, /i, '')}` : msg.replace(/^Value error, /i, '')
      })
      .join(' • ')
  }

  if (typeof detail === 'string') {
    return detail
  }

  if (detail && typeof detail === 'object') {
    return detail.message || JSON.stringify(detail)
  }

  return 'Request failed'
}

async function refreshTokens() {
  if (refreshPromise) {
    return refreshPromise
  }

  refreshPromise = fetch(`${BASE_URL}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: getRefreshToken() }),
  }).then(async (response) => {
    const data = await safeJson(response)
    if (!response.ok) {
      throw new Error(normalizeErrorPayload(data?.detail || 'Session expired'))
    }

    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    return data
  }).finally(() => {
    refreshPromise = null
  })

  return refreshPromise
}

async function request(endpoint, options = {}) {
  const {
    method = 'GET',
    body,
    query,
    noAuth = false,
    skipRefresh = false,
    raw = false,
  } = options

  const url = `${BASE_URL}${endpoint}${query ? buildQuery(query) : ''}`
  const headers = {
    ...(options.headers || {}),
    ...(body && !(body instanceof FormData) ? { 'Content-Type': 'application/json' } : {}),
  }

  if (!noAuth) {
    const token = getAccessToken()
    if (token) {
      headers.Authorization = `Bearer ${token}`
    }
  }

  let response = await fetch(url, {
    method,
    headers,
    body: body ? (body instanceof FormData ? body : JSON.stringify(body)) : undefined,
  })

  if (response.status === 401 && !noAuth && !skipRefresh && !AUTH_ROUTES.some((route) => endpoint.startsWith(route))) {
    try {
      await refreshTokens()
      const retryHeaders = { ...headers }
      retryHeaders.Authorization = `Bearer ${getAccessToken()}`
      response = await fetch(url, {
        method,
        headers: retryHeaders,
        body: body ? (body instanceof FormData ? body : JSON.stringify(body)) : undefined,
      })
    } catch (error) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.href = '/login'
      throw error
    }
  }

  if (!response.ok) {
    const data = await safeJson(response)
    throw new Error(normalizeErrorPayload(data?.detail || 'Request failed'))
  }

  if (raw) {
    return response
  }

  if (response.status === 204) {
    return null
  }

  return response.json()
}

export const api = {
  register: (payload) => request('/auth/register', { method: 'POST', body: payload, noAuth: true }),
  login: (payload) => request('/auth/login', { method: 'POST', body: payload, noAuth: true }),
  refresh: (payload) => request('/auth/refresh', { method: 'POST', body: payload, noAuth: true, skipRefresh: true }),
  logout: () => request('/auth/logout', { method: 'POST' }),
  me: () => request('/auth/me'),

  listEvents: (query) => request('/events', { query }),
  getEvent: (eventId) => request(`/events/${eventId}`),
  createEvent: (payload) => request('/events', { method: 'POST', body: payload }),
  updateEvent: (eventId, payload) => request(`/events/${eventId}`, { method: 'PATCH', body: payload }),
  deleteEvent: (eventId) => request(`/events/${eventId}`, { method: 'DELETE' }),
  cancelEvent: (eventId) => request(`/events/${eventId}/cancel`, { method: 'POST' }),
  listCategories: () => request('/events/categories'),

  listBookings: (query) => request('/bookings', { query }),
  createBooking: (payload) => request('/bookings', { method: 'POST', body: payload }),
  cancelBooking: (bookingId) => request(`/bookings/${bookingId}/cancel`, { method: 'POST' }),

  listNotifications: (query) => request('/notifications', { query }),
  markNotificationRead: (notificationId) => request(`/notifications/${notificationId}/read`, { method: 'PATCH' }),
  markNotificationUnread: (notificationId) => request(`/notifications/${notificationId}/unread`, { method: 'PATCH' }),
  markAllNotificationsRead: () => request('/notifications/read-all', { method: 'POST' }),

  listReviews: (eventId, query) => request(`/reviews/events/${eventId}`, { query }),
  createReview: (eventId, payload) => request(`/reviews/events/${eventId}`, { method: 'POST', body: payload }),
  updateReview: (reviewId, payload) => request(`/reviews/${reviewId}`, { method: 'PATCH', body: payload }),
  deleteReview: (reviewId) => request(`/reviews/${reviewId}`, { method: 'DELETE' }),

  listUsers: (query) => request('/users', { query }),
  updateUser: (userId, payload) => request(`/users/${userId}`, { method: 'PATCH', body: payload }),
  deleteUser: (userId) => request(`/users/${userId}`, { method: 'DELETE' }),
  updateProfile: (payload) => request('/users/me', { method: 'PATCH', body: payload }),
  changePassword: (payload) => request('/users/me/change-password', { method: 'POST', body: payload }),

  listAuditLogs: (query) => request('/audit-logs', { query }),
  getHealth: () => request('/health', { noAuth: true }),
}

export { BASE_URL, WS_BASE_URL }
