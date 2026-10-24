import { useState, useEffect, useCallback } from 'react'
import { format } from 'date-fns'
import { api } from '../api'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'

function StarRating({ value, onChange }) {
  const [hover, setHover] = useState(0)
  return (
    <div className="star-group">
      {[1, 2, 3, 4, 5].map(n => (
        <span
          key={n}
          className={`star${n <= (hover || value) ? ' active' : ''}`}
          onClick={() => onChange(n)}
          onMouseEnter={() => setHover(n)}
          onMouseLeave={() => setHover(0)}
        >★</span>
      ))}
    </div>
  )
}

export default function ReviewSection({ eventId }) {
  const { user } = useAuth()
  const { show } = useToast()
  const [reviews, setReviews] = useState([])
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState({ rating: 5, comment: '', parent_review_id: null })
  const [submitting, setSubmitting] = useState(false)
  const [replyTo, setReplyTo] = useState(null) // { id, authorName }
  const [editId, setEditId] = useState(null)

  const load = useCallback(async () => {
    try {
      const d = await api.listReviews(eventId)
      setReviews(Array.isArray(d) ? d : (d?.items || []))
    } catch {}
    setLoading(false)
  }, [eventId])

  useEffect(() => { load() }, [load])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      const payload = { rating: form.rating, comment: form.comment }
      if (replyTo) payload.parent_review_id = replyTo.id
      if (editId) {
        await api.updateReview(editId, { rating: form.rating, comment: form.comment })
        show('Review updated!', 'success')
        setEditId(null)
      } else {
        await api.createReview(eventId, payload)
        show('Review posted!', 'success')
      }
      setForm({ rating: 5, comment: '', parent_review_id: null })
      setReplyTo(null)
      load()
    } catch (err) {
      show(err.message, 'error')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (reviewId) => {
    if (!confirm('Delete this review?')) return
    try {
      await api.deleteReview(reviewId)
      show('Deleted', 'success')
      load()
    } catch (err) {
      show(err.message, 'error')
    }
  }

  const startEdit = (r) => {
    setEditId(r.id)
    setForm({ rating: r.rating, comment: r.comment })
    setReplyTo(null)
  }

  const startReply = (r) => {
    setReplyTo({ id: r.id, authorName: r.user_email || 'reviewer' })
    setEditId(null)
    setForm({ rating: 5, comment: '' })
  }

  if (loading) return <div className="spinner" />

  return (
    <div>
      <h2 style={{ fontWeight: 700, marginBottom: '1rem', fontSize: '1.1rem' }}>
        Reviews ({reviews.length})
      </h2>

      {/* Review form */}
      {user && (
        <div className="card" style={{ marginBottom: '1.25rem' }}>
          {replyTo && (
            <div className="alert alert-info" style={{ marginBottom: '.75rem' }}>
              Replying to <strong>{replyTo.authorName}</strong>
              <button className="btn btn-ghost btn-sm" style={{ marginLeft: '.5rem' }} onClick={() => setReplyTo(null)}>✕</button>
            </div>
          )}
          {editId && (
            <div className="alert alert-info" style={{ marginBottom: '.75rem' }}>
              Editing review
              <button className="btn btn-ghost btn-sm" style={{ marginLeft: '.5rem' }} onClick={() => { setEditId(null); setForm({ rating: 5, comment: '' }) }}>✕</button>
            </div>
          )}

          <form onSubmit={handleSubmit}>
            {!replyTo && (
              <div className="form-group">
                <label>Rating</label>
                <StarRating value={form.rating} onChange={v => setForm(f => ({ ...f, rating: v }))} />
              </div>
            )}
            <div className="form-group">
              <label>Comment</label>
              <textarea
                className="form-control"
                placeholder={replyTo ? 'Write a reply…' : 'Write a review…'}
                value={form.comment}
                onChange={e => setForm(f => ({ ...f, comment: e.target.value }))}
                required
              />
              <span className="text-muted text-sm">Mention a user with @email@example.com.</span>
            </div>
            <button type="submit" className="btn btn-primary btn-sm" disabled={submitting}>
              {submitting ? 'Posting…' : (editId ? 'Update' : replyTo ? 'Post reply' : 'Post review')}
            </button>
          </form>
        </div>
      )}

      {/* Reviews list */}
      {reviews.length === 0 ? (
        <p className="text-muted text-sm">No reviews yet. Be the first!</p>
      ) : (
        reviews.map(r => {
          const isMyReview = user && (user.id === r.user_id || (r.user_email && user.email === r.user_email) || user.role === 'admin')
          return (
            <div key={r.id} className="review-card">
              <div className="review-header">
                <div>
                  <span className="review-author">{r.user_email || 'Attendee'}</span>
                  {r.rating && (
                    <span className="review-rating" style={{ marginLeft: '.5rem' }}>
                      {'★'.repeat(r.rating)}{'☆'.repeat(5 - r.rating)}
                    </span>
                  )}
                </div>
                <div style={{ display: 'flex', gap: '.4rem', alignItems: 'center' }}>
                  <span className="text-muted text-sm">{format(new Date(r.created_at), 'MMM d, yyyy')}</span>
                  {isMyReview && (
                    <>
                      {(user.id === r.user_id || user.role === 'admin') && <button className="btn btn-ghost btn-sm" onClick={() => startEdit(r)}>Edit</button>}
                      <button className="btn btn-danger btn-sm" onClick={() => handleDelete(r.id)}>Delete</button>
                    </>
                  )}
                </div>
              </div>
              <p className="review-body">{r.comment}</p>

              {user && (
                <button className="btn btn-ghost btn-sm" style={{ marginTop: '.5rem' }} onClick={() => startReply(r)}>
                  Reply
                </button>
              )}

              {/* Replies */}
              {r.replies?.length > 0 && (
                <div className="review-replies">
                  {r.replies.map(rep => {
                    const isMyReply = user && (user.id === rep.user_id || (rep.user_email && user.email === rep.user_email) || user.role === 'admin')
                    return (
                      <div key={rep.id} className="reply-card">
                        <div className="review-header">
                          <span className="review-author" style={{ fontSize: '.8rem' }}>{rep.user_email || 'Organizer'}</span>
                          <div style={{ display: 'flex', gap: '.4rem', alignItems: 'center' }}>
                            <span className="text-muted text-sm">{format(new Date(rep.created_at), 'MMM d')}</span>
                            {isMyReply && (
                              <button className="btn btn-danger btn-sm" onClick={() => handleDelete(rep.id)}>Delete</button>
                            )}
                          </div>
                        </div>
                        <p className="review-body">{rep.comment}</p>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          )
        })
      )}
    </div>
  )
}
