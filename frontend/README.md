# EventDesk Frontend

React application for discovering events and managing bookings, reviews, notifications, and organizer/admin workflows. It uses the FastAPI API in the repository and live WebSocket channels for ticket and notification updates.

## Requirements

- Node.js 20.19+ or 22.12+
- The EventDesk API running locally at `http://localhost:8000`

## Setup

From this directory, install dependencies and start Vite:

```sh
npm install
npm run dev
```

Vite serves the app at `http://localhost:5173` by default.

The API and WebSocket URLs default to the local backend. To override them, copy `.env.example` to `.env.local` and set `VITE_API_BASE_URL` and `VITE_WS_BASE_URL`.

## Checks

```sh
npm run build
npm run lint
```

`ENDPOINT_COVERAGE.md` maps frontend screens to API routes. `BACKEND_GAPS.md` records API limitations and the corresponding frontend behavior.
