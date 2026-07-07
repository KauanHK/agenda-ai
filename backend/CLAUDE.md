# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run the API (dev)
uv run uvicorn app.main:app --host 0.0.0.0 --port 8745

# Database migrations
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic revision --autogenerate -m "description"

# Tests
uv run pytest                         # all tests
uv run pytest tests/modules/users/   # specific module
uv run pytest -v                      # verbose

# Linting / formatting
uv run ruff check ./app --fix
uv run ruff check ./app/modules/users/ --fix

# Background workers
uv run celery -A app.celery_app worker --loglevel=info
uv run celery -A app.celery_app beat --loglevel=info

# Docker (full stack)
docker-compose up
```

## Architecture

FastAPI + SQLAlchemy 2.0 async + PostgreSQL. Clean Architecture with DDD module layout. Each feature module under `app/modules/{feature}/` follows a fixed internal structure:

```
modules/{feature}/
├── api/
│   ├── router.py        # HTTP endpoints (FastAPI router)
│   └── deps.py          # Module-specific dependency injection
├── domain/
│   ├── model.py         # SQLAlchemy ORM model
│   ├── schemas.py       # Pydantic schemas (request/response)
│   ├── enums.py         # Domain enumerations
│   └── filters.py       # Query filter definitions
├── application/
│   ├── read.py          # Query use cases
│   ├── create.py        # Creation use cases
│   ├── update.py        # Update use cases
│   └── delete.py        # Deletion use cases
└── infra/
    └── repository.py    # SQLAlchemy data access
```

All modules are wired into `app/api/router.py`.

### Key layers

- **`app/core/`** — settings (pydantic-settings), JWT/bcrypt security, custom exception hierarchy, exception handlers, CORS middleware, pagination models.
- **`app/db/`** — async session factory, Unit of Work pattern (`unit_of_work.py`), SQLAlchemy `DeclarativeBase`.
- **`app/api/deps/`** — shared FastAPI dependencies: current user extraction, DB session, pagination params.
- **`app/worker/`** — Celery tasks; `app/celery_app.py` configures Redis broker/backend.
- **`app/integrations/`** — Google OAuth2, WhatsApp Evolution API.

### Auth flow

JWT-based with two token types: access (30 min) and refresh (7 days). Security helpers live in `app/core/security.py`. Role-based access uses `UserRole` enum — roles include `GLOBAL_ADMIN` and `ESTABLISHMENT_ADMIN` for multi-tenant scoping.

### Multi-tenancy

Requests are scoped by `establishment_id`. Repository queries filter by establishment based on the authenticated user's role.

### Testing patterns

Tests mirror the module tree under `tests/`. API tests use a mock FastAPI app with dependency overrides (see `conftest.py` files). Use cases are tested independently with mocked repositories. Async tests run automatically via `asyncio_mode = "auto"` set in `pyproject.toml`.
