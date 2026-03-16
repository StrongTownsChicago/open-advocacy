# Open Advocacy

Open Advocacy is an open-source web application connecting citizens with representatives and tracking advocacy projects. It allows users to look up their representatives, track advocacy projects, and understand where representatives stand on various issues, including a multi-issue scorecard view for comparing representative alignment across projects.

## Current Project Features

- **Project Tracking**: View active advocacy projects with details on their status
- **Representative Lookup**: Find your representatives by entering your address
- **Status Visualization**: See color-coded representations of where representatives stand on issues
- **Multi-Issue Scorecard**: Compare representatives across multiple advocacy projects with alignment scores
- **Geographic Integration**: Utilizes geospatial data to accurately match addresses to districts
- **Authentication & User Management**: Role-based access control with user registration, login, and admin functionality
- **Flexible Data Import System**: Extensible framework for importing location-specific data from various sources (Chicago City Council, Illinois legislature, Chicago City Clerk voting records)
- **Custom Dashboards**: Slug-based project dashboards with configurable labels and status displays

## Tech Stack

- **Backend**: FastAPI with SQLAlchemy 2.0 ORM and Pydantic models (Python 3.12)
- **Frontend**: React 19 with TypeScript, Vite, and Material UI
- **Database**: PostgreSQL/PostGIS (production) or SQLite (development)
- **Containerization**: Docker and Docker Compose for easy deployment
- **Deployment**: Railway

## Data Model

The application uses the following core concepts:

- **Projects**: Advocacy initiatives that can be tracked and monitored
- **Entities**: Representatives or officials who have a position on projects
- **Jurisdictions**: Legislative bodies (e.g., City Council, State Senate)
- **Districts**: Geographic areas represented by entities
- **Status Records**: Track where entities stand on specific projects (`solid_approval`, `leaning_approval`, `neutral`, `leaning_disapproval`, `solid_disapproval`, `unknown`)
- **Users & Groups**: User management with role-based permissions

## User Roles & Permissions

- **Public**: Can view projects, look up representatives, see status distributions and scorecards
- **Editors**: Can create/edit projects and update entity statuses
- **Group Admins**: Can manage users within their group and have editor permissions
- **Super Admins**: Full system access including user management across all groups

## Backend Architecture

- **API Layer**: FastAPI routes that handle HTTP requests and responses
- **Service Layer**: Business logic organized by domain entities (including `scorecard_service.py` for cross-project alignment scoring)
- **Data Access Layer**: Abstract database providers with concrete implementations for SQLite and PostgreSQL
- **Authentication Layer**: JWT-based auth with role-based access control
- **Geo Services**: Specialized geographic functionality (PostGIS in production, Shapely in development)
- **Import System**: Modular framework for importing location-specific data
- **Models**: Pydantic models for validation and ORM models for persistence

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/products/docker-desktop/) and Docker Compose for the simplest setup
- Alternatively for local development:
  - Python 3.12 with [Poetry](https://python-poetry.org/docs/)
  - Node.js 18+ with npm

### Running the Application with Docker Compose

The easiest way to get started is using Docker Compose, which will run frontend, backend, and postgres containers:

```bash
docker-compose up
```

Once running, you can access:

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Auto-Initialization

On first startup, the backend automatically creates database tables, creates an admin user, and seeds data based on environment variables:

- `ADMIN_USERNAME` — Email address for the auto-created super admin user
- `ADMIN_PASSWORD` — Password for the auto-created super admin user
- `SEED_LOCATIONS` — Comma-separated locations to import (e.g. `chicago`, `chicago,illinois`)
- `SEED_PROJECTS` — Comma-separated project sets to seed (e.g. `adu`, `example`, `scorecard`)

If both `ADMIN_USERNAME` and `ADMIN_PASSWORD` are set, a super admin account is created automatically on cold start. If either is absent, no admin user is created and you must run `python -m scripts.add_super_admin` manually.

Initialization is skipped on subsequent starts if the database tables already exist.

### Setting Up Data Manually

To populate the database manually (outside Docker):

1. Navigate to the backend directory and activate Poetry:

   ```bash
   cd backend
   poetry shell
   ```

2. Initialize the database:

   ```bash
   python -m scripts.init_db
   ```

3. Import location data:

   ```bash
   python -m scripts.import_data chicago      # Chicago City Council + wards + alderpersons
   python -m scripts.import_data illinois     # Illinois House/Senate districts + legislators
   ```

4. Seed project data:

   ```bash
   python -m scripts.import_example_project_data   # Generic example projects
   python -m scripts.import_adu_project_data        # ADU Opt-In project (Chicago-specific)
   python -m scripts.import_scorecard_projects      # Scorecard projects from City Clerk data
   ```

5. Create a super admin user:
   ```bash
   python -m scripts.add_super_admin
   ```
   Alternatively, set `ADMIN_USERNAME` and `ADMIN_PASSWORD` environment variables before running the app and the super admin will be created automatically on cold start.

#### Import System Options

The import system supports selective importing:

```bash
# Import only specific steps
python -m scripts.import_data chicago --steps "Import Chicago City Council jurisdiction" "Import Chicago Alderpersons"

# Import only jurisdictions and districts (skip entities)
python -m scripts.import_data chicago --steps "Import Chicago City Council jurisdiction" "Import Chicago Wards GeoJSON"
```

## Project Structure

```
open-advocacy/
├── backend/                     # FastAPI backend service
│   ├── app/                     # Application code
│   │   ├── api/                 # API endpoints
│   │   │   └── routes/          # API route handlers
│   │   │       ├── admin/       # Admin-specific routes
│   │   │       │   ├── imports.py
│   │   │       │   └── users.py
│   │   │       ├── auth.py      # Authentication routes
│   │   │       ├── entities.py  # Entity management routes
│   │   │       ├── groups.py    # Group management routes
│   │   │       ├── jurisdictions.py
│   │   │       ├── projects.py  # Project management routes
│   │   │       ├── scorecard.py # Multi-project scorecard endpoint
│   │   │       └── status.py    # Status tracking routes
│   │   ├── core/                # Core configuration
│   │   │   ├── auth.py          # Authentication utilities
│   │   │   └── config.py        # Application configuration
│   │   ├── db/                  # Database utilities
│   │   ├── geo/                 # Geospatial utilities
│   │   ├── imports/             # Import system
│   │   │   ├── base.py          # Base classes for imports
│   │   │   ├── orchestrator.py  # Import orchestration
│   │   │   ├── importers/       # Specific data importers
│   │   │   │   ├── jurisdiction_importer.py
│   │   │   │   ├── district_importer.py
│   │   │   │   └── entity_importer.py
│   │   │   ├── locations/       # Location-specific configurations
│   │   │   │   ├── base.py      # Base location config
│   │   │   │   ├── chicago.py   # Chicago import configuration
│   │   │   │   └── illinois.py  # Illinois import configuration
│   │   │   └── sources/         # Data source implementations
│   │   │       ├── chicago_alderpersons.py        # Chicago Open Data API
│   │   │       ├── chicago_city_clerk_elms.py     # City Clerk vote/sponsorship data
│   │   │       ├── geojson.py                     # GeoJSON file handler
│   │   │       ├── openstates.py                  # OpenStates API integration
│   │   │       └── ward_zoning.py                 # Cityscape zoning data
│   │   ├── models/              # Data models
│   │   │   ├── orm/             # SQLAlchemy ORM models
│   │   │   └── pydantic/        # Pydantic validation models
│   │   ├── services/            # Business logic services
│   │   │   ├── entity_service.py
│   │   │   ├── group_service.py
│   │   │   ├── project_service.py
│   │   │   ├── scorecard_service.py  # Cross-project alignment scoring
│   │   │   ├── status_service.py
│   │   │   ├── user_service.py
│   │   │   └── service_factory.py
│   │   └── data/                # Auto-generated data caches
│   │       ├── elms_scorecard_data.py   # City Clerk vote/sponsorship cache
│   │       └── ward_zoning_data.py      # Ward zoning percentages cache
│   ├── scripts/                 # Setup and maintenance scripts
│   │   ├── add_super_admin.py          # Create super admin user
│   │   ├── fetch_elms_scorecard_data.py # Fetch/refresh City Clerk eLMS data
│   │   ├── fetch_ward_zoning_data.py   # Fetch ward zoning data from Cityscape
│   │   ├── import_adu_project_data.py  # Seed ADU Opt-In project
│   │   ├── import_data.py              # Main data import script
│   │   ├── import_example_project_data.py # Seed example projects
│   │   ├── import_scorecard_projects.py   # Seed scorecard projects from eLMS data
│   │   ├── init_db.py                  # Database initialization
│   │   └── initialize_app.py           # Auto-run startup initialization
│   └── tests/                   # Backend tests
├── frontend/                    # React+TypeScript frontend
│   ├── e2e/                     # Playwright end-to-end tests
│   └── src/                     # Application source code
│       ├── components/          # Reusable UI components
│       │   ├── auth/            # Authentication components
│       │   ├── common/          # Common UI components
│       │   ├── Entity/          # Entity-specific components
│       │   ├── Project/         # Project-specific components
│       │   └── Status/          # Status visualization components
│       ├── contexts/            # React contexts
│       │   ├── AuthContext.tsx  # Authentication state management
│       │   └── UserRepresentativesContext.tsx
│       ├── hooks/               # Custom React hooks
│       ├── pages/               # Page components
│       │   ├── admin/           # Admin-specific pages
│       │   │   ├── AdminDashboard.tsx
│       │   │   ├── DataImportPage.tsx   # Trigger data imports
│       │   │   ├── RegisterPage.tsx     # User registration
│       │   │   └── UserManagementPage.tsx
│       │   ├── CustomProjects/  # Project-specific dashboards
│       │   │   └── AduOptInDashboard.tsx
│       │   ├── EntityDetail.tsx
│       │   ├── HomePage.tsx
│       │   ├── LoginPage.tsx
│       │   ├── ProjectDashboard.tsx  # Generic slug-based dashboard
│       │   ├── ProjectDetail.tsx
│       │   ├── ProjectFormPage.tsx   # Create/edit projects
│       │   ├── ProjectList.tsx
│       │   ├── RepresentativeLookup.tsx
│       │   └── Scorecard.tsx         # Multi-project alignment scorecard
│       ├── services/            # API services
│       │   ├── api.ts           # Base Axios configuration
│       │   ├── auth.ts
│       │   ├── scorecard.ts     # Scorecard API calls
│       │   └── ...              # Other service files
│       ├── types/               # TypeScript type definitions
│       └── utils/               # Utility functions
└── docker-compose.yaml          # Docker Compose configuration
```

## Import System Architecture

The application features a modular import system designed to handle location-specific data from various sources:

### Key Components

- **Data Sources**: Abstract interfaces for fetching data from APIs, files, or databases
- **Importers**: Specialized classes for importing specific types of data (jurisdictions, districts, entities)
- **Location Configs**: Configuration classes that define import steps for specific locations
- **Orchestrator**: Coordinates the import process and handles step dependencies

### Supported Data Sources

- **Chicago Open Data API**: Official alderperson data
- **Chicago City Clerk eLMS API**: Vote and sponsorship records for scorecard projects
- **OpenStates API**: State legislator information (requires `OPENSTATES_API_KEY`)
- **GeoJSON Files**: District boundary data with automatic validation
- **Cityscape API**: Ward zoning data (requires `CHICAGO_CITYSCAPE_API_KEY`)

### Refreshing Cached Data

Some data sources generate static Python cache files that are committed to the repo:

```bash
# Refresh City Clerk vote/sponsorship data (writes app/data/elms_scorecard_data.py)
python -m scripts.fetch_elms_scorecard_data

# Refresh ward zoning percentages (writes app/data/ward_zoning_data.py)
python -m scripts.fetch_ward_zoning_data
```

### Adding New Locations

1. Create a location configuration in `app/imports/locations/`
2. Define the import steps (jurisdictions, districts, entities)
3. Configure data sources (APIs, files, etc.)
4. Register the location in the import orchestrator
5. Run: `python -m scripts.import_data your_location`

## Configuration

Key environment variables:

| Variable                       | Description                                                                              |
| ------------------------------ | ---------------------------------------------------------------------------------------- |
| `DATABASE_PROVIDER`            | `sqlite` (default) or `postgres`                                                         |
| `DATABASE_URL`                 | Database connection string                                                               |
| `AUTH_SECRET_KEY`              | Secret key for JWT token generation                                                      |
| `ENVIRONMENT`                  | `development` or `production`                                                            |
| `ALLOWED_ORIGIN`               | CORS origin (defaults to `localhost:3000` and `localhost:5173`)                          |
| `ADMIN_USERNAME`               | Email for the super admin created on cold start (set with `ADMIN_PASSWORD` to enable)    |
| `ADMIN_PASSWORD`               | Password for the super admin created on cold start (set with `ADMIN_USERNAME` to enable) |
| `OPENSTATES_API_KEY`           | Required for Illinois legislature imports                                                |
| `CHICAGO_CITYSCAPE_API_KEY`    | Required for ward zoning data script                                                     |
| `SEED_LOCATIONS`               | Locations to seed on cold start (e.g. `chicago`, `chicago,illinois`)                     |
| `SEED_PROJECTS`                | Project sets to seed on cold start (e.g. `adu`, `example`, `scorecard`)                  |
| `VITE_API_URL`                 | Frontend API base URL override                                                           |
| `VITE_APPLICATION_NAME`        | App display name (default: `Open Advocacy`)                                              |
| `VITE_APPLICATION_DESCRIPTION` | App tagline                                                                              |

See `backend/app/core/config.py` for all available options.

## License

This project is licensed under the MIT License
