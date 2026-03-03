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
python -m scripts.initialize_app          # Full initialization (DB + Chicago import + ADU project seed)
python -m scripts.import_adu_project_data # Seed ADU opt-in project data
python -m scripts.import_example_project_data # Seed example projects

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

- **Backend**: FastAPI + SQLAlchemy 2.0 (Python 3.12) — note: no Alembic migrations; tables are created via `init_db` at startup
- **Frontend**: React 19 + TypeScript + Vite + Material UI + Leaflet maps + react-markdown
- **Database**: PostgreSQL/PostGIS in production, SQLite in development
- **Deployment**: Railway

### Backend Structure

The backend follows a layered architecture:

```
API Routes (app/api/routes/) → Service Layer (app/services/) → DB Providers (app/db/) → ORM Models (app/models/orm/)
```

- **`app/main.py`** — FastAPI app with CORS and logging middleware; triggers `initialize_application()` on startup (see Auto-Initialization below)
- **`app/core/config.py`** — All configuration via env vars (DATABASE_PROVIDER, DATABASE_URL, AUTH_SECRET_KEY, OPENSTATES_API_KEY, etc.)
- **`app/core/auth.py`** — JWT auth, OAuth2, password hashing
- **`app/db/`** — Abstract `DatabaseProvider` interface; `SQLProvider` supports both SQLite and PostgreSQL
- **`app/geo/`** — Geographic lookup layer: abstract `GeoProvider` interface with `PostgresGeoProvider` (PostGIS) and `SQLiteGeoProvider` (Shapely) implementations, plus `geocoding_service.py` and `provider_factory.py`. Used by `EntityService` for address-to-district resolution.
- **`app/services/`** — Business logic; `service_factory.py` provides three tiers of DI: plain `create_*()` factories, FastAPI `Depends()`-compatible `get_*()` functions, and `@lru_cache` singletons (`get_cached_*()`) for script use
- **`app/imports/`** — Modular data import system: `locations/` configs, `sources/` data fetchers, `importers/` processors, `orchestrator.py` coordinator
- **`app/scripts/`** — Older utility scripts (`seed_dummy_data.py`, `db_diagnostic.py`, `import_chicago_ward_geojson.py`, etc.)

### Auto-Initialization on Startup

On first startup, `app/main.py` calls `scripts/initialize_app.py:initialize_application()`, which:
1. Creates DB tables
2. Imports Chicago alderperson + ward data
3. Seeds the ADU Opt-In project

A lock file at `/tmp/open_advocacy_db_initialized` prevents re-running on subsequent restarts. Delete this file to force re-initialization (e.g., after a schema change in dev).

### Frontend Structure

- **`src/services/api.ts`** — Axios client; base URL from `VITE_API_URL` or falls back to the hardcoded production Railway URL; forces HTTPS on all requests
- **`src/contexts/`** — `AuthContext` (JWT auth state), `UserRepresentativesContext` (user's reps)
- **`src/pages/`** — Route-level components; `admin/` for admin pages, `CustomProjects/` for location-specific projects (e.g. ADU tracker)
- **`src/components/`** — Shared UI components organized by domain (`Entity/`, `Project/`, `Status/`, `auth/`, `common/`)
- **`src/utils/config.ts`** — App name/description branding from `VITE_APPLICATION_NAME` / `VITE_APPLICATION_DESCRIPTION`

### Data Model

Core entities with UUID primary keys:

- **Group** — Organizes users and projects; each project and user belongs to a group
- **Project** — Advocacy initiatives with `status` + `preferred_status` (EntityStatus enum), linked to a `Jurisdiction` and `Group`
- **Entity** — Representatives/officials with contact info and `entity_type`
- **EntityStatusRecord** — Links entities to projects with position data (EntityStatus: `solid_approval`, `leaning_approval`, `neutral`, `leaning_disapproval`, `solid_disapproval`, `unknown`)
- **Jurisdiction** / **District** — Legislative bodies and geographic areas (GeoJSON boundaries)
- **User** — Role-based: `super_admin`, `group_admin`, `editor`, `viewer`

### Environment Variables

Key variables (set in `.env` for local dev, Railway for production):

- `DATABASE_PROVIDER` — `sqlite` (default) or `postgres`
- `DATABASE_URL` — Connection string
- `ENVIRONMENT` — `development` or `production`
- `ALLOWED_ORIGIN` — CORS origin; defaults to both `localhost:3000` and `localhost:5173`
- `AUTH_SECRET_KEY` — JWT signing secret (required for auth to work)
- `OPENSTATES_API_KEY` — For state legislature data imports (required for Illinois import)
- `ADMIN_USERNAME` — Default admin username in dev (default: `admin`)
- `GEOCODING_SERVICE` — Optional geocoding provider (`google`, `mapbox`, etc.)
- `GEOCODING_API_KEY` — API key for geocoding provider
- `DATA_DIR` — Override the data directory path
- `VITE_API_URL` — (Frontend) Override API base URL; without this, production Railway URL is used as fallback
- `VITE_APPLICATION_NAME` — (Frontend) App display name (default: `Strong Towns Chicago Advocacy Tracker`)
- `VITE_APPLICATION_DESCRIPTION` — (Frontend) App tagline

### Adding a New Import Location

1. Create `backend/app/imports/locations/<location>.py` with location config and import steps
2. Add data sources under `app/imports/sources/` if needed
3. Register in `app/imports/orchestrator.py`
4. Run `python -m scripts.import_data <location>`
