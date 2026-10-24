# EventDesk

EventDesk is an event discovery and ticket booking application. The backend is a FastAPI service backed by PostgreSQL; the React frontend is a small browser client for attendee, organizer, and admin workflows.

## Requirements

- Python 3.14 and [uv](https://docs.astral.sh/uv/)
- PostgreSQL
- Node.js 20.19+ or 22.12+

## Setup

Create a local environment file and update its database URL and secret key:

```sh
cp .env.example .env
```

Do not use the example secret key outside local development. Keep `.env` local; it is ignored by Git.

Install Python dependencies and apply database migrations:

```sh
uv sync --all-groups
uv run alembic upgrade head
```

Start the API from the repository root:

```sh
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API documentation is available at `http://localhost:8000/docs`; the OpenAPI document is at `http://localhost:8000/api/v1/openapi.json`.

Start the React client in a second terminal:

```sh
cd frontend
npm ci
npm run dev
```

The frontend defaults to `http://localhost:8000/api/v1` and `ws://localhost:8000/api/v1`. Override these with `VITE_API_BASE_URL` and `VITE_WS_BASE_URL` in `frontend/.env.local` if needed.

## Tests and Checks

Run the backend test suite from the repository root:

```sh
uv run pytest -q
```

Run the frontend checks from `frontend/`:

```sh
npm run build
npm run lint
```

## Features

- Email/password registration and login, hashed passwords, JWT access/refresh tokens, and role-protected routes.
- Event creation and management, discovery filters, sorting, pagination, and organizer/admin stats.
- Ticket bookings for all roles with row-level locking to prevent overselling, plus cancellation and soft deletion.
- Display names, profile updates, admin user soft deletion, reviews, one-level replies, mentions, notifications, and audit logs.
- WebSocket ticket and notification updates, scheduled event reminders, and automatic event completion.

The data model diagram is in [event_desk_erd.png](event_desk_erd.png). The frontend endpoint map and known API limitations are documented in [frontend/ENDPOINT_COVERAGE.md](frontend/ENDPOINT_COVERAGE.md) and [frontend/BACKEND_GAPS.md](frontend/BACKEND_GAPS.md).

## Remaining Gaps Against the Requirements

- The API does not include event/entity identifiers in notification payloads, so the UI cannot always link a notification directly to its resource.
- There is no organizer-facing attendee list or export endpoint.
- Password reset, MFA, payments, seat selection, waiting lists, and recurring events are not implemented; these are optional bonuses in the brief.
