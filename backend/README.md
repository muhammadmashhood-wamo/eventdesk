# EventDesk Backend

FastAPI backend service for EventDesk.

## Setup

```bash
uv sync --all-groups
uv run alembic upgrade head
```

## Running the Server

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Tests

```bash
uv run pytest -q
```
