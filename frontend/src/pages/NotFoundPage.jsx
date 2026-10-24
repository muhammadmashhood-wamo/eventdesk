import { Link } from 'react-router-dom'

export default function NotFoundPage() {
  return (
    <div className="page">
      <div className="container narrow">
        <div className="empty-state card">
          <h3>Page not found</h3>
          <p>The page you requested does not exist or is no longer available.</p>
          <div className="mt-2">
            <Link to="/events" className="btn btn-primary">Back to events</Link>
          </div>
        </div>
      </div>
    </div>
  )
}
