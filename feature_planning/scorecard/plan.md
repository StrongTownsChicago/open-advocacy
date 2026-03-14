# Feature: Multi-Issue Alderperson Scorecard

## Problem Statement

The Strong Towns Chicago instance of Open Advocacy currently tracks only one project: the ADU ward opt-in dashboard. The goal is to expand this to a multi-issue scorecard covering 7 additional legislative actions — votes and co-sponsorships — that alderpersons have taken on housing and transportation issues. Visitors should be able to see each alderperson's full record across all tracked issues at a glance.

The work divides into four concrete phases:

1. A Legistar API client that fetches vote and sponsorship data from the public Chicago Legistar web API
2. An import script that seeds the 8 scorecard projects and populates EntityStatusRecords from Legistar data
3. A backend `/api/scorecard` endpoint that returns a combined cross-project payload without N+1 queries
4. A frontend `/scorecard` page with a sortable, color-coded table and mobile card fallback

---

## Current State Analysis

### Existing patterns this feature must follow

- **Import scripts** (`backend/scripts/import_adu_project_data.py`, `import_example_project_data.py`) use `get_cached_*()` service factories from `service_factory.py` and run via `asyncio.run()`. No orchestrator integration is required for the scorecard importer.
- **Data sources** (`backend/app/imports/sources/chicago_alderpersons.py`) subclass `DataSource` from `app/imports/base.py` and expose `fetch_data()` / `get_source_info()`.
- **Project idempotency**: `project_service.create_project()` does NOT guard against duplicate slugs itself; the import script must check for an existing project by slug before calling `create_project()`.
- **Status upsert**: `status_service.create_status_record()` already performs an upsert by `(entity_id, project_id)`, so re-running the import is safe.
- **API routes** are registered directly in `app/main.py` via `app.include_router(...)` — there is no separate `router.py` file.
- **Frontend services** call the axios client in `src/services/api.ts`. Each domain gets its own service file (e.g., `src/services/projects.ts`).
- **Frontend types** live in `src/types/index.ts` — new response shapes should be added there.
- **Status colors** are centralized in `src/utils/statusColors.ts` and used via `getStatusColor()` / `makeStatusLabelFn()`.

### Key files

| File | Relevance |
|---|---|
| `backend/scripts/import_adu_project_data.py` | Canonical import script pattern to follow |
| `backend/app/imports/sources/chicago_alderpersons.py` | Canonical DataSource pattern |
| `backend/app/services/service_factory.py` | `get_cached_*()` / `get_*()` / `create_*()` tiers |
| `backend/app/services/status_service.py` | Upsert logic |
| `backend/app/services/project_service.py` | `get_project_by_slug()` for idempotency check |
| `backend/app/models/pydantic/models.py` | `EntityStatus`, `DashboardConfig`, `ProjectBase` |
| `backend/app/main.py` | Router registration |
| `frontend/src/types/index.ts` | Type definitions |
| `frontend/src/App.tsx` | Route registration |
| `frontend/src/components/common/Header.tsx` | Nav links |

---

## Proposed Solution

### Architecture Decisions

**Decision 1: Legistar client as a DataSource subclass vs. a standalone class**

- **Options considered:** (A) Subclass `DataSource` from `app/imports/base.py`; (B) Plain class with no base class
- **Chosen:** B — plain class
- **Rationale:** `DataSource` is designed for fetching a single homogeneous list for the importer pipeline. The Legistar client must perform three distinct API call types (matter lookup, sponsor fetch, vote fetch) with different return shapes and async chaining. Forcing these into a single `fetch_data()` method produces a confusing interface. A plain `LegistarClient` class with three focused async methods is cleaner and more testable.

**Decision 2: Scorecard endpoint — new route file vs. adding to existing entities/projects routes**

- **Options considered:** (A) Add `/scorecard` endpoint to `entities.py` or `projects.py`; (B) New `scorecard.py` route file
- **Chosen:** B — new route file
- **Rationale:** The scorecard endpoint has a distinct response shape that crosses multiple services (projects + entities + status records). Adding it to an existing route file violates SRP. A dedicated file keeps routing concerns separated and makes the endpoint easy to find.

**Decision 3: Scorecard data assembly — service layer vs. directly in route**

- **Options considered:** (A) Build a `ScorecardService` with full DI; (B) Assemble the scorecard payload directly in the route using existing service instances
- **Chosen:** A — dedicated `ScorecardService`
- **Rationale:** The alignment score logic (counting matches between entity status and project `preferred_status`) is pure business logic and should be unit-testable without HTTP layer involvement. A service class keeps the route handler thin and the logic testable. The service only needs read access to providers already available through `service_factory.py`.

**Decision 4: Group resolution on the frontend**

- **Options considered:** (A) Hardcode the Strong Towns Chicago group UUID as a `VITE_SCORECARD_GROUP_ID` env var; (B) Pass `group_id` as a query param from a config constant; (C) Have the backend resolve the group by a well-known name and omit group_id from the API contract
- **Chosen:** A — `VITE_SCORECARD_GROUP_ID` env var, with the frontend passing it as `?group_id=`
- **Rationale:** Option C hides the group resolution in the backend and makes the endpoint less reusable for other deployments. Option B with a hardcoded UUID in source code is the same as A but without the deployment flexibility of env vars. `VITE_SCORECARD_GROUP_ID` follows the existing `VITE_APPLICATION_NAME` pattern.

**Decision 5: Name normalization for Legistar entity matching**

- **Options considered:** (A) Exact string match; (B) Lowercase + strip; (C) Full normalize (lowercase, strip, collapse whitespace, strip punctuation)
- **Chosen:** C — full normalization
- **Rationale:** Legistar names (e.g., "Ald. Maria Hadden") may include titles, extra spaces, or punctuation that don't match the entity names in the DB (e.g., "Maria Hadden"). A normalize function applied to both sides prevents silent mismatches. Unmatched names should be logged as warnings, not silently dropped.

### Implementation Approach

Follow existing script patterns exactly. The Legistar client is the only truly new abstraction; everything else reuses existing services, models, and patterns.

---

## Detailed Implementation Steps

### Step 1: Legistar API client

**New file:** `backend/app/imports/sources/legistar.py`

A plain async class (not a `DataSource` subclass) with three focused methods, plus a name normalization helper. Uses `aiohttp` (already a dependency via `chicago_alderpersons.py`).

**Methods:**

```python
class LegistarClient:
    BASE_URL = "https://webapi.legistar.com/v1/chicago"

    async def get_matter_id(self, guid: str) -> int | None
    # GET /matters?$filter=MatterGuid eq '{guid}'
    # Returns the numeric MatterId or None if not found

    async def get_matter_sponsors(self, matter_id: int) -> list[dict]
    # GET /matters/{matter_id}/sponsors
    # Returns list of {MatterSponsorName, MatterSponsorSequence, ...}

    async def get_matter_votes(self, matter_id: int) -> list[dict] | None
    # GET /matters/{matter_id}/histories to find the Common Council final passage EventItemId
    # GET /eventitems/{EventItemId}/votes
    # Returns None if no council vote found, otherwise list of {VotePersonName, VoteValueName, ...}
```

**Vote → EventItem lookup logic:** The histories endpoint returns a list of history records. The target record has `MatterHistoryActionName` containing "final passage" (case-insensitive) and `MatterHistoryRollCallFlag` equal to 1. Use the first matching record's `MatterHistoryEventItemId`.

**Name normalization:**
```python
def normalize_name(name: str) -> str:
    """Lowercase, strip whitespace, remove punctuation for fuzzy name matching."""
```

**Vote value → EntityStatus mapping** (hardcoded in the client module as a dict constant):
| Legistar `VoteValueName` | `EntityStatus` |
|---|---|
| `Yea` | `SOLID_APPROVAL` |
| `Nay` | `SOLID_DISAPPROVAL` |
| `Abstain` / `Recuse` | `NEUTRAL` |
| `Absent` / `Not Voting` (any other) | `UNKNOWN` |

**Sponsor → EntityStatus mapping:**
| Condition | `EntityStatus` |
|---|---|
| `MatterSponsorSequence == 1` (primary sponsor) | `SOLID_APPROVAL` |
| Any other sequence (cosponsor) | `SOLID_APPROVAL` |
| Not in sponsor list | `UNKNOWN` |

Both sponsorship roles map to `SOLID_APPROVAL` because the scorecard label ("Cosponsored") is the same for both. The distinction between primary/co-sponsor is irrelevant for alignment scoring but can be preserved in `notes` if needed.

**Files to create:**
- `backend/app/imports/sources/legistar.py`

---

### Step 2: Import script

**New file:** `backend/scripts/import_scorecard_projects.py`

Follows `import_adu_project_data.py` exactly: `get_cached_*()` factories, `asyncio.run()` entrypoint, per-project logging.

**Project definitions** (hardcoded `SCORECARD_PROJECTS` list in the script):

```python
SCORECARD_PROJECTS = [
    {
        "slug": "single-stair-ordinance",
        "title": "Single Stair Ordinance — Cosponsors",
        "description": "...",
        "matter_guid": "9F0FF51D-7036-F011-8C4D-001DD8309E73",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": {
            "solid_approval": "Cosponsored",
            "unknown": "Not a Cosponsor",
        },
    },
    {
        "slug": "cha-housing-ordinance",
        "title": "CHA Housing Ordinance — Cosponsors",
        "description": "...",
        "matter_guid": "7F84A4EE-7136-F011-8C4D-001DD8309E73",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": {
            "solid_approval": "Cosponsored",
            "unknown": "Not a Cosponsor",
        },
    },
    {
        "slug": "adu-citywide-vote",
        "title": "ADU Citywide Expansion — Vote",
        "description": "...",
        "matter_guid": "54028B60-C4FC-EE11-A1FE-001DD804AF4C",
        "import_type": "vote",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": {
            "solid_approval": "Voted Yes",
            "solid_disapproval": "Voted No",
            "neutral": "Abstained",
            "unknown": "Absent/Not Voting",
        },
    },
    {
        "slug": "adu-citywide-sponsorship",
        "title": "ADU Citywide Expansion — Cosponsors",
        "description": "...",
        "matter_guid": "54028B60-C4FC-EE11-A1FE-001DD804AF4C",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": {
            "solid_approval": "Cosponsored",
            "unknown": "Not a Cosponsor",
        },
    },
    # ... No Parking Minimums vote + sponsorship, HED Bond vote + sponsorship
]
```

**Script flow for each project:**
1. Check if project with that slug already exists (`project_service.get_project_by_slug()`). If it exists, skip creation and use the existing project ID. This is the idempotency guard missing from `create_project()`.
2. If not found, create `ProjectBase` with `title`, `description`, `status=ACTIVE`, `preferred_status`, `jurisdiction_id`, `group_id`, `slug`, `dashboard_config=DashboardConfig(representative_title="Alderperson", status_labels=...)`.
3. Look up `MatterId` via `LegistarClient.get_matter_id(matter_guid)`. If None, log error and skip status imports for this project.
4. Based on `import_type`:
   - `"vote"`: call `client.get_matter_votes(matter_id)`. Build a `{normalized_name: VoteValueName}` dict.
   - `"sponsorship"`: call `client.get_matter_sponsors(matter_id)`. Build a `{normalized_name: sequence}` dict.
5. Fetch all entities for the Chicago City Council jurisdiction.
6. For each entity, normalize its name and look it up in the Legistar response dict. Map to `EntityStatus` using the constants. Entities not found in the Legistar data get `EntityStatus.UNKNOWN`.
7. Call `status_service.create_status_record()` for each entity (upsert behavior is already implemented).

**Files to create:**
- `backend/scripts/import_scorecard_projects.py`

---

### Step 3: Scorecard service and backend endpoint

**New file:** `backend/app/services/scorecard_service.py`

```python
class ScorecardService:
    def __init__(
        self,
        projects_provider: DatabaseProvider,
        entities_provider: DatabaseProvider,
        status_records_provider: DatabaseProvider,
        districts_provider: DatabaseProvider,
    ): ...

    async def get_scorecard(self, group_id: UUID) -> ScorecardResponse:
        # 1. Fetch all active projects for the group in one query
        # 2. Get the jurisdiction_id from the first project (all scorecard projects share Chicago City Council)
        # 3. Fetch all entities for that jurisdiction in one query
        # 4. Fetch all status records for those project_ids + entity_ids in one query
        # 5. Build entity rows: for each entity, look up status per project, compute alignment score
        # 6. Return ScorecardResponse
```

**New Pydantic models** (add to `backend/app/models/pydantic/models.py`):

```python
class ScorecardProject(BaseModel):
    id: UUID
    title: str
    slug: str | None
    preferred_status: EntityStatus
    status_labels: dict[str, str] | None

class ScorecardEntityStatus(BaseModel):
    status: EntityStatus
    label: str  # resolved from project's status_labels

class ScorecardEntityRow(BaseModel):
    entity: Entity
    statuses: dict[str, ScorecardEntityStatus]  # keyed by project_id as str
    aligned_count: int
    total_scoreable: int  # projects with preferred_status set

class ScorecardResponse(BaseModel):
    projects: list[ScorecardProject]
    entities: list[ScorecardEntityRow]
```

**New file:** `backend/app/api/routes/scorecard.py`

```
GET /api/scorecard?group_id={uuid}
```

No authentication required (public endpoint). Returns `ScorecardResponse`. Returns 422 if `group_id` is missing.

**Register in `backend/app/main.py`:**

```python
from app.api.routes import scorecard
app.include_router(scorecard.router, prefix="/api/scorecard", tags=["scorecard"])
```

**Add to `service_factory.py`:**

```python
def create_scorecard_service(...) -> ScorecardService: ...
def get_scorecard_service(...) -> ScorecardService: ...  # FastAPI Depends version
```

**Files to create:**
- `backend/app/services/scorecard_service.py`
- `backend/app/api/routes/scorecard.py`

**Files to modify:**
- `backend/app/models/pydantic/models.py` — add 4 new Pydantic models
- `backend/app/services/service_factory.py` — add `create_scorecard_service()` and `get_scorecard_service()`
- `backend/app/main.py` — register the scorecard router

---

### Step 4: Frontend scorecard page

**New file:** `frontend/src/services/scorecard.ts`

```typescript
export const scorecardService = {
  getScorecard: (groupId: string) =>
    api.get<ScorecardResponse>('/scorecard', { params: { group_id: groupId } }),
};
```

**New types** (add to `frontend/src/types/index.ts`):

```typescript
export interface ScorecardProject {
  id: string;
  title: string;
  slug?: string;
  preferred_status: EntityStatus;
  status_labels?: Record<string, string>;
}

export interface ScorecardEntityStatus {
  status: EntityStatus;
  label: string;
}

export interface ScorecardEntityRow {
  entity: Entity;
  statuses: Record<string, ScorecardEntityStatus>;  // keyed by project_id
  aligned_count: number;
  total_scoreable: number;
}

export interface ScorecardResponse {
  projects: ScorecardProject[];
  entities: ScorecardEntityRow[];
}
```

**New file:** `frontend/src/pages/Scorecard.tsx`

- Reads `VITE_SCORECARD_GROUP_ID` from `import.meta.env` (falls back to empty string with a logged warning)
- Calls `scorecardService.getScorecard(groupId)` on mount
- Renders a MUI `Table` with sticky header
- Rows: one per alderperson, sorted by alignment score descending by default
- Columns: ward (from `entity.district_name`), alderperson name (links to `/representatives/{id}`), one column per project, alignment score ("4 / 8")
- Cells: MUI `Chip` colored via `getStatusColor(status)` with the label from `ScorecardEntityStatus.label`
- Column headers: abbreviated project title (full title in a `Tooltip`)
- Sort controls: clickable column headers for name, ward, and alignment score
- Mobile breakpoint (`xs`): collapse table to one `Card` per alderperson listing each issue as a labeled row
- Loading state: `CircularProgress` centered
- Error state: `ErrorDisplay` component (already exists at `src/components/common/ErrorDisplay.tsx`)

**Modify `frontend/src/App.tsx`:**
Add `<Route path="/scorecard" element={<Scorecard />} />` alongside the other public routes.

**Modify `frontend/src/components/common/Header.tsx`:**
Add `/scorecard` with label `"Scorecard"` to the nav paths array. The existing `isActive()` logic handles the active underline automatically.

**Modify `frontend/src/utils/config.ts`:**
Add `VITE_SCORECARD_GROUP_ID` export (read from `import.meta.env.VITE_SCORECARD_GROUP_ID`).

**Files to create:**
- `frontend/src/services/scorecard.ts`
- `frontend/src/pages/Scorecard.tsx`

**Files to modify:**
- `frontend/src/types/index.ts` — add 4 new interfaces
- `frontend/src/App.tsx` — add `/scorecard` route
- `frontend/src/components/common/Header.tsx` — add Scorecard nav link
- `frontend/src/utils/config.ts` — add `VITE_SCORECARD_GROUP_ID`

---

## Edge Cases & Error Handling

| Scenario | Handling Strategy | Impact |
|---|---|---|
| Legistar API returns 429 or 5xx | Log error, raise exception with matter_guid context; script fails fast on HTTP errors | Import aborts; re-run after delay |
| Matter GUID not found in Legistar | Log warning, skip status import for that project; project record is still created | Project shows all unknown statuses |
| Legistar vote history has no "final passage" record | `get_matter_votes()` returns `None`; script logs warning and skips vote import | Project shows all unknown statuses |
| Entity name in Legistar doesn't match DB (after normalization) | Log warning with both names; entity gets `UNKNOWN` status | Alignment score will be low; fixable by adjusting normalization or name data |
| `VITE_SCORECARD_GROUP_ID` not set | Log warning in console; API call returns 422; Scorecard page shows error state | Page displays error; fixable by setting env var |
| Group has no active scorecard projects | Endpoint returns empty `projects` and `entities` lists | Frontend renders empty table with a "No scorecard data" message |
| Project has no `preferred_status` | Alignment score denominator excludes that project (`total_scoreable` is unaffected); count still correct | No impact on alignment score computation |
| Import run twice (re-run idempotency) | Slug check prevents duplicate project creation; status upsert overwrites existing records | Safe to re-run; data is refreshed |
| Alderperson count mismatch (vacancy, new election) | Script uses the live entity list from the DB; no hardcoded counts | Graceful; new alderpersons get UNKNOWN |

---

## Testing Strategy

### Unit Tests to Write

**`backend/tests/test_legistar_client.py`**

These tests mock `aiohttp.ClientSession` to avoid real HTTP calls.

- `test_get_matter_id_returns_numeric_id()` — mock response with one matter record, assert correct ID extracted
- `test_get_matter_id_returns_none_when_not_found()` — mock empty list response
- `test_get_matter_votes_finds_final_passage_event()` — mock histories with one matching record (`RollCallFlag=1`, action contains "final passage"), assert correct EventItemId used
- `test_get_matter_votes_returns_none_when_no_final_passage()` — mock histories with no matching records
- `test_get_matter_sponsors_returns_list()` — mock sponsor response, assert list returned
- `test_normalize_name_strips_titles_and_punctuation()` — pure function, no mocking needed
  - "Ald. Maria Hadden" → "maria hadden"
  - "BURNETT JR., WALTER" → "burnett jr walter"
  - "  Carlos  Ramirez-Rosa  " → "carlos ramirezrosa"

**`backend/tests/test_scorecard_service.py`**

Uses `MockDatabaseProvider` from `tests/mock_provider.py`.

- `test_get_scorecard_computes_alignment_score()` — seed 2 projects and 2 entities; one entity has `solid_approval` on project 1 (preferred_status=`solid_approval`) and `solid_disapproval` on project 2; assert `aligned_count=1`, `total_scoreable=2`
- `test_get_scorecard_entity_with_no_status_record_gets_unknown()` — seed project + entity with no status record; assert entity row has `UNKNOWN` status
- `test_get_scorecard_returns_empty_when_no_projects()` — empty projects list; assert `ScorecardResponse` has empty lists
- `test_get_scorecard_resolves_status_labels_from_project()` — project has `status_labels={"solid_approval": "Voted Yes"}`; entity has `solid_approval`; assert `ScorecardEntityStatus.label == "Voted Yes"`

**`backend/tests/test_api_scorecard.py`**

- `test_scorecard_endpoint_no_auth_required()` — GET `/api/scorecard?group_id=...` returns 200 without token
- `test_scorecard_endpoint_missing_group_id_returns_422()` — GET `/api/scorecard` without param returns 422
- `test_scorecard_endpoint_returns_correct_shape()` — mock ScorecardService, assert response has `projects` and `entities` keys

### Frontend Unit Tests to Write

**`frontend/src/pages/Scorecard.test.tsx`**

- `test renders loading state initially` — mock service to hang; assert CircularProgress visible
- `test renders error state when API fails` — mock service to reject; assert error message visible
- `test renders table with correct columns` — mock service with 2 projects and 1 entity; assert project title columns and entity name row visible
- `test renders alignment score correctly` — mock entity with `aligned_count=3, total_scoreable=8`; assert "3 / 8" visible

### Manual Testing Checklist

- [ ] Run `python -m scripts.import_scorecard_projects` — confirm "8 projects created/found" in logs
- [ ] Verify ~400 EntityStatusRecords in DB (50 alderpersons × 8 projects)
- [ ] `GET /api/scorecard?group_id={id}` — verify JSON has `projects` array (length 8) and `entities` array (length 50)
- [ ] Visit `/scorecard` — table renders with all 8 project columns
- [ ] Click alderperson name — navigates to `/representatives/{id}`
- [ ] Sort by alignment score — rows reorder
- [ ] Resize to mobile — cards render instead of table
- [ ] Visit `/dashboard/adu-citywide-vote` — existing project dashboard still works with vote labels
- [ ] Re-run import script — no duplicate projects created, status records are updated

---

## Files Affected

**Created:**
- `backend/app/imports/sources/legistar.py` — Legistar API client
- `backend/app/services/scorecard_service.py` — cross-project alignment logic
- `backend/app/api/routes/scorecard.py` — GET /api/scorecard endpoint
- `backend/scripts/import_scorecard_projects.py` — project seed + status import
- `backend/tests/test_legistar_client.py` — unit tests for Legistar client
- `backend/tests/test_scorecard_service.py` — unit tests for ScorecardService
- `backend/tests/test_api_scorecard.py` — API route tests
- `frontend/src/services/scorecard.ts` — API service
- `frontend/src/pages/Scorecard.tsx` — scorecard page
- `frontend/src/pages/Scorecard.test.tsx` — frontend unit tests

**Modified:**
- `backend/app/models/pydantic/models.py` — add `ScorecardProject`, `ScorecardEntityStatus`, `ScorecardEntityRow`, `ScorecardResponse`
- `backend/app/services/service_factory.py` — add `create_scorecard_service()` and `get_scorecard_service()`
- `backend/app/main.py` — register scorecard router
- `frontend/src/types/index.ts` — add 4 new interfaces
- `frontend/src/App.tsx` — add `/scorecard` route
- `frontend/src/components/common/Header.tsx` — add Scorecard nav link
- `frontend/src/utils/config.ts` — export `VITE_SCORECARD_GROUP_ID`

**Documentation:**
- [ ] Update `CLAUDE.md` — add `import_scorecard_projects` to the scripts table, add `VITE_SCORECARD_GROUP_ID` to env vars section

---

## Rollout Considerations

- **No database migrations needed** — no new tables or columns; all data uses existing `projects` and `entity_status_records` tables
- **Backwards compatible** — the scorecard endpoint is additive; no existing routes are changed
- **Feature flags** — not needed; the page is only reachable by navigating to `/scorecard` or clicking the nav link
- **Deployment sequence:**
  1. Deploy backend with new scorecard endpoint and `import_scorecard_projects` script
  2. Run `python -m scripts.import_scorecard_projects` in Railway console
  3. Deploy frontend with scorecard page and nav link
  4. Set `VITE_SCORECARD_GROUP_ID` in Railway frontend env vars
- **`VITE_SCORECARD_GROUP_ID` value**: The UUID of the "Strong Towns Chicago" group. Obtain by querying `GET /api/groups` after backend deploy, or reading from DB. The `import_adu_project_data.py` script already creates this group via `find_or_create_by_name()`.

---

## Success Criteria

- [ ] `python -m scripts.import_scorecard_projects` runs without errors on a fresh DB (Chicago data already imported)
- [ ] All 8 scorecard projects are created with correct slugs, titles, and `dashboard_config`
- [ ] `GET /api/scorecard?group_id={id}` returns 200 with correct JSON shape
- [ ] Each entity row has `statuses` keyed by all 8 project IDs
- [ ] Alignment scores are accurate (manually verify 2–3 alderpersons against Legistar data)
- [ ] `/scorecard` page renders without console errors
- [ ] Scorecard table is sortable by name, ward, and alignment score
- [ ] Mobile card view renders on viewport width < 600px
- [ ] Existing ADU opt-in dashboard at `/dashboard/adu-opt-in-dashboard` is unaffected
- [ ] `poetry run pytest` — all tests pass
- [ ] `poetry run ruff check .` — no warnings
- [ ] `poetry run mypy .` — no errors
- [ ] `npm run lint` — no warnings
- [ ] `npm run type-check` — no errors
- [ ] `npm test` — all tests pass
