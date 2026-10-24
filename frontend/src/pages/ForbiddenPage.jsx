import { Link } from 'react-router-dom'

export default function ForbiddenPage() {
  return (
    <div className="page">
      <div className="container narrow">
        <div className="empty-state card">
          <h3>Access denied</h3>
          <p>You do not have permission to view this page.</p>
          <div className="mt-2">
            <Link to="/events" className="btn btn-primary">Return home</Link>
          </div>
        </div>
      </div>
    </div>
  )
}
