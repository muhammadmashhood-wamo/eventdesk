import { useMemo, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { CalendarRange, Filter, Search, SlidersHorizontal, Plus } from 'lucide-react'
import { api } from '../api'
import { useAuth } from '../context/AuthContext'

const PAGE_SIZE_OPTIONS = [10, 20, 50]

export default function EventsPage() {
  const { user } = useAuth()
  const [searchParams, setSearchParams] = useSearchParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const page = Number(searchParams.get('page') || 1)
  const limit = Number(searchParams.get('limit') || 20)
  const search = searchParams.get('search') || ''
  const category = searchParams.get('category') || ''
  const organizerId = searchParams.get('organizer_id') || ''
  const dateFrom = searchParams.get('date_from') || ''
  const dateTo = searchParams.get('date_to') || ''
  const tag = searchParams.get('tag') || ''
  const minPrice = searchParams.get('min_price') || ''
  const maxPrice = searchParams.get('max_price') || ''
  const sortBy = searchParams.get('sort_by') || ''
  const status = searchParams.get('status') || ''

  const filters = useMemo(() => ({
    skip: (page - 1) * limit,
    limit,
    search: search || undefined,
    category: category || undefined,
    organizer_id: organizerId || undefined,
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
    tag: tag || undefined,
    min_price: minPrice || undefined,
    max_price: maxPrice || undefined,
    sort_by: sortBy || undefined,
    status: status || undefined,
  }), [page, limit, search, category, organizerId, dateFrom, dateTo, tag, minPrice, maxPrice, sortBy, status])

  const { data, isLoading, isError } = useQuery({
    queryKey: ['events', filters],
    queryFn: () => api.listEvents(filters),
  })

  const categories = useMemo(() => {
    const values = (data?.items || []).map((item) => item.category).filter(Boolean)
    return [...new Set(values)]
  }, [data])

  const updateFilters = (updates) => {
    const next = new URLSearchParams(searchParams)
    Object.entries(updates).forEach(([key, value]) => {
      if (!value) {
        next.delete(key)
      } else {
        next.set(key, value)
      }
    })
    next.set('page', '1')
    setSearchParams(next)
  }

  const clearFilters = () => {
    setSearchParams({ page: '1', limit: String(limit) })
  }

  const pageCount = Math.max(1, Math.ceil((data?.total || 0) / limit))
  const isOrganizerOrAdmin = user && (user.isOrganizer || user.isAdmin)

  const handleCreate = () => navigate('/events/new')

  const handleRefetchOnFocus = () => {
    queryClient.invalidateQueries({ queryKey: ['events'] })
  }

  return (
    <div className="page-shell">
      <div className="hero">
        <div className="hero-inner">
          <div>
            <p className="eyebrow">Discover the next thing</p>
            <h1>Find the event that fits your next plan.</h1>
          </div>
          {isOrganizerOrAdmin && (
            <button className="btn btn-primary" onClick={handleCreate}>
              <Plus size={16} /> Create event
            </button>
          )}
        </div>
      </div>

      <div className="container narrow">
        <div className="panel filter-panel">
          <div className="field search-field">
            <Search size={16} />
            <input
              type="search"
              value={search}
              placeholder="Search title, description, venue"
              onChange={(event) => updateFilters({ search: event.target.value })}
            />
          </div>

          <div className="filter-grid">
            <div className="field">
              <label>Category</label>
              <input
                list="category-suggestions"
                aria-label="Category"
                value={category}
                onChange={(event) => updateFilters({ category: event.target.value })}
              />
              <datalist id="category-suggestions">
                {categories.map((item) => (
                  <option key={item} value={item} />
                ))}
              </datalist>
            </div>

            <div className="field">
              <label htmlFor="event-tag-filter">Tag</label>
              <input
                id="event-tag-filter"
                value={tag}
                onChange={(event) => updateFilters({ tag: event.target.value })}
              />
            </div>

            <div className="field">
              <label htmlFor="event-organizer-filter">Organizer ID</label>
              <input
                id="event-organizer-filter"
                value={organizerId}
                onChange={(event) => updateFilters({ organizer_id: event.target.value })}
              />
            </div>

            <div className="field">
              <label htmlFor="event-date-from">From</label>
              <input
                id="event-date-from"
                type="date"
                value={dateFrom}
                onChange={(event) => updateFilters({ date_from: event.target.value })}
              />
            </div>

            <div className="field">
              <label htmlFor="event-date-to">To</label>
              <input
                id="event-date-to"
                type="date"
                value={dateTo}
                onChange={(event) => updateFilters({ date_to: event.target.value })}
              />
            </div>

            <div className="field">
              <label htmlFor="event-min-price">Minimum price</label>
              <input
                id="event-min-price"
                type="number"
                min="0"
                step="0.01"
                value={minPrice}
                onChange={(event) => updateFilters({ min_price: event.target.value })}
              />
            </div>

            <div className="field">
              <label htmlFor="event-max-price">Maximum price</label>
              <input
                id="event-max-price"
                type="number"
                min="0"
                step="0.01"
                value={maxPrice}
                onChange={(event) => updateFilters({ max_price: event.target.value })}
              />
            </div>

            <div className="field">
              <label htmlFor="event-sort">Sort by</label>
              <select id="event-sort" value={sortBy} onChange={(event) => updateFilters({ sort_by: event.target.value })}>
                <option value="">Event date (ascending)</option>
                <option value="date_desc">Event date (descending)</option>
                <option value="price_asc">Price (low to high)</option>
                <option value="price_desc">Price (high to low)</option>
                <option value="created_at_desc">Recently added</option>
                <option value="title_asc">Title (A to Z)</option>
              </select>
            </div>

            {isOrganizerOrAdmin && (
              <div className="field">
                <label htmlFor="event-status">Status</label>
                <select id="event-status" value={status} onChange={(event) => updateFilters({ status: event.target.value })}>
                  <option value="">Published events</option>
                  <option value="Draft">Draft</option>
                  <option value="Published">Published</option>
                  <option value="Cancelled">Cancelled</option>
                  <option value="Completed">Completed</option>
                </select>
              </div>
            )}

            <div className="field inline-field">
              <label htmlFor="event-page-size">Page size</label>
              <select
                id="event-page-size"
                value={limit}
                onChange={(event) => setSearchParams({ ...Object.fromEntries(searchParams.entries()), limit: event.target.value, page: '1' })}
              >
                {PAGE_SIZE_OPTIONS.map((option) => (
                  <option key={option} value={option}>{option}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="toolbar-row">
            <button className="btn btn-ghost" onClick={clearFilters}>
              <SlidersHorizontal size={14} /> Clear filters
            </button>
            <button className="btn btn-ghost" onClick={handleRefetchOnFocus}>
              <CalendarRange size={14} /> Refresh
            </button>
          </div>
        </div>

        {isLoading && <div className="page-loading">Loading events…</div>}

        {!isLoading && isError && (
          <div className="empty-state">
            <Filter size={36} />
            <h3>Events could not be loaded</h3>
            <p>Please refresh the page or try again.</p>
          </div>
        )}

        {!isLoading && !isError && data?.items?.length === 0 && (
          <div className="empty-state">
            <Search size={36} />
            <h3>No matches found</h3>
            <p>Try a different search or clear the date/category filters.</p>
          </div>
        )}

        {!isLoading && !isError && data?.items?.length > 0 && (
          <>
            <div className="event-grid">
              {data.items.map((event) => (
                <Link key={event.id} to={`/events/${event.id}`} className="event-card-link">
                  <article className="event-card">
                    <div className="card-top-row">
                      <span className={`status-badge ${event.status?.toLowerCase()}`}>{event.status}</span>
                      <span className="meta">{event.category || 'General'}</span>
                    </div>
                    <h3>{event.title}</h3>
                    <p className="meta-line">{event.venue}</p>
                    <p className="meta-line">{new Date(event.event_date).toLocaleString()}</p>
                    <div className="tag-row">
                      {(event.tags || []).slice(0, 4).map((tag) => (
                        <span key={`${event.id}-${tag}`} className="tag-chip">{tag}</span>
                      ))}
                    </div>
                    <div className="card-bottom-row">
                      <strong>{new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(Number(event.ticket_price || 0))}</strong>
                      <span>{event.available_tickets} left / {event.total_tickets}</span>
                    </div>
                  </article>
                </Link>
              ))}
            </div>

            <div className="pagination-row">
              <button className="btn btn-ghost" disabled={page <= 1} onClick={() => setSearchParams({ ...Object.fromEntries(searchParams.entries()), page: String(page - 1) })}>
                Previous
              </button>
              <span>Page {page} of {pageCount}</span>
              <button className="btn btn-ghost" disabled={page >= pageCount} onClick={() => setSearchParams({ ...Object.fromEntries(searchParams.entries()), page: String(page + 1) })}>
                Next
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
