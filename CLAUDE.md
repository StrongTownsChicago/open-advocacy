# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Open Advocacy is a civic engagement platform for tracking legislative advocacy projects and representatives. It consists of a FastAPI backend, React/TypeScript frontend, and a PostgreSQL/PostGIS database, deployed on Railway.

## Development Commands

### Backend

```bash
cd backend
poetry shell                              # Activate virtualenv
python run.py                             # Dev server on port 8000

# Database management
python -m scripts.init_db                 # Initialize DB tables
python -m scripts.import_data chicago     # Import Chicago data
python -m scripts.import_data illinois    # Import Illinois data
python -m scripts.add_super_admin         # Create super admin user
python -m scripts.initialize_app          # Full initialization

# Code quality
poetry run ruff check .                   # Lint
poetry run ruff format .                  # Format
poetry run mypy .                         # Type check
poetry run pytest                         # Run tests
```

### Frontend

```bash
cd frontend
npm run dev           # Dev server on port 3000
npm run build         # Production build
npm run lint          # ESLint
npm run lint:fix      # Auto-fix lint issues
npm run format        # Prettier format
npm run type-check    # TypeScript check
```

### Docker (full stack)

```bash
docker-compose up     # Start postgres + backend + frontend
```

## Architecture

### Stack

- **Backend**: FastAPI + SQLAlchemy 2.0 + Alembic (Python 3.12)
- **Frontend**: React 19 + TypeScript + Vite + Material UI + Leaflet maps
- **Database**: PostgreSQL/PostGIS in production, SQLite in development
- **Deployment**: Railway

### Backend Structure

The backend follows a layered architecture:

```
API Routes (app/api/routes/) → Service Layer (app/services/) → DB Providers (app/db/) → ORM Models (app/models/orm/)
```

- **`app/main.py`** — FastAPI app with CORS and logging middleware
- **`app/core/config.py`** — All configuration via env vars (DATABASE_PROVIDER, DATABASE_URL, AUTH_SECRET_KEY, OPENSTATES_API_KEY, etc.)
- **`app/core/auth.py`** — JWT auth, OAuth2, password hashing
- **`app/db/`** — Abstract `DatabaseProvider` interface; `SQLProvider` supports both SQLite and PostgreSQL
- **`app/services/`** — Business logic; `service_factory.py` provides DI with both transient and cached instances
- **`app/imports/`** — Modular data import system: `locations/` configs, `sources/` data fetchers, `importers/` processors, `orchestrator.py` coordinator

### Frontend Structure

- **`src/services/api.ts`** — Axios client (base URL from `VITE_API_URL` or hardcoded production URL); forces HTTPS
- **`src/contexts/`** — `AuthContext` (JWT auth state), `UserRepresentativesContext` (user's reps)
- **`src/pages/`** — Route-level components; `admin/` for admin pages, `CustomProjects/` for location-specific projects (e.g. ADU tracker)
- **`src/components/`** — Shared UI components organized by domain (`Entity/`, `Project/`, `Status/`, `auth/`, `common/`)

### Data Model

Core entities with UUID primary keys:

- **Project** — Advocacy initiatives with `status` + `preferred_status`, linked to a `Jurisdiction` and `Group`
- **Entity** — Representatives/officials with contact info and `entity_type`
- **EntityStatusRecord** — Links entities to projects with position data
- **Jurisdiction** / **District** — Legislative bodies and geographic areas (GeoJSON boundaries)
- **User** — Role-based: `SUPER_ADMIN`, `GROUP_ADMIN`, `EDITOR`, `VIEWER`

### Environment Variables

Key variables (set in `.env` for local dev, Railway for production):

- `DATABASE_PROVIDER` — `sqlite` (default) or `postgres`
- `DATABASE_URL` — Connection string
- `ENVIRONMENT` — `development` or `production`
- `ALLOWED_ORIGIN` — CORS origin (default: `localhost:3000`)
- `AUTH_SECRET_KEY` — JWT signing secret
- `OPENSTATES_API_KEY` — For state legislature data imports
- `VITE_API_URL` — (Frontend) Override API base URL

### Adding a New Import Location

1. Create `backend/app/imports/locations/<location>.py` with location config and import steps
2. Add data sources under `app/imports/sources/` if needed
3. Register in `app/imports/orchestrator.py`
4. Run `python -m scripts.import_data <location>`
