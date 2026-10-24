import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Navbar from './components/Navbar'
import ProtectedRoute from './components/ProtectedRoute'
import { AuthProvider } from './context/AuthContext'
import { ToastProvider } from './context/ToastContext'
import AdminUsersPage from './pages/AdminUsersPage'
import AuditLogsPage from './pages/AuditLogsPage'
import BookingsPage from './pages/BookingsPage'
import DashboardPage from './pages/DashboardPage'
import EventDetailPage from './pages/EventDetailPage'
import EventFormPage from './pages/EventFormPage'
import EventsPage from './pages/EventsPage'
import ForbiddenPage from './pages/ForbiddenPage'
import LoginPage from './pages/LoginPage'
import MyEventsPage from './pages/MyEventsPage'
import NotFoundPage from './pages/NotFoundPage'
import NotificationsPage from './pages/NotificationsPage'
import ProfilePage from './pages/ProfilePage'
import RegisterPage from './pages/RegisterPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: true,
      staleTime: 15000,
    },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <ToastProvider>
            <Navbar />
            <Routes>
              <Route path="/" element={<Navigate to="/events" replace />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/events" element={<EventsPage />} />
              <Route path="/events/:id" element={<EventDetailPage />} />
              <Route path="/events/new" element={<ProtectedRoute roles={['organizer', 'admin']}><EventFormPage /></ProtectedRoute>} />
              <Route path="/events/:id/edit" element={<ProtectedRoute roles={['organizer', 'admin']}><EventFormPage /></ProtectedRoute>} />
              <Route path="/dashboard" element={<ProtectedRoute roles={['organizer', 'admin']}><DashboardPage /></ProtectedRoute>} />
              <Route path="/my-events" element={<ProtectedRoute roles={['organizer', 'admin']}><MyEventsPage /></ProtectedRoute>} />
              <Route path="/bookings" element={<ProtectedRoute><BookingsPage /></ProtectedRoute>} />
              <Route path="/notifications" element={<ProtectedRoute><NotificationsPage /></ProtectedRoute>} />
              <Route path="/profile" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
              <Route path="/admin/users" element={<ProtectedRoute roles={['admin']}><AdminUsersPage /></ProtectedRoute>} />
              <Route path="/admin/audit" element={<ProtectedRoute roles={['admin']}><AuditLogsPage /></ProtectedRoute>} />
              <Route path="/admin/audit-logs" element={<ProtectedRoute roles={['admin']}><AuditLogsPage /></ProtectedRoute>} />
              <Route path="/403" element={<ForbiddenPage />} />
              <Route path="*" element={<NotFoundPage />} />
            </Routes>
          </ToastProvider>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
