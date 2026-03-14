# Technical Analysis: Multi-Issue Scorecard

## Codebase Exploration Findings

### Relevant Files Explored

| File | Key Finding |
|---|---|
| `backend/scripts/import_adu_project_data.py` | Canonical script pattern: `get_cached_*()` factories, `asyncio.run()`, per-entity logging. **No slug idempotency guard** — `create_project()` is called unconditionally. The scorecard script must add a `get_project_by_slug()` check. |
| `backend/app/services/project_service.py` | `create_project()` does not check for duplicate slugs. It validates group and jurisdiction exist but has no uniqueness enforcement. Duplicate slug handling must live in the import script. |
| `backend/app/services/status_service.py` | `create_status_record()` performs an upsert by `(entity_id, project_id)`. Re-running the import script is safe. |
| `backend/app/imports/sources/chicago_alderpersons.py` | Uses `aiohttp.ClientSession`. This is the library to use for the Legistar client — already in the dependency tree. |
| `backend/app/imports/base.py` | `DataSource` base class has a single `fetch_data()` method. Not appropriate for the Legistar client which needs three distinct async operations with different return shapes. |
| `backend/app/main.py` | Routes are registered directly with `app.include_router()`. There is no separate `router.py` aggregator. The scorecard router must be added here. |
| `backend/app/services/service_factory.py` | Three tiers: `create_*()` (plain), `get_*()` (FastAPI Depends), `get_cached_*()` (lru_cache singleton for scripts). The scorecard service needs `create_scorecard_service()` and `get_scorecard_service()`. The cached version is not needed since the import script uses existing cached services. |
| `backend/app/models/pydantic/models.py` | All domain models are in one file. New scorecard response models go here. `DashboardConfig` already has `status_labels: dict[str, str] | None` — reuse this for resolving cell labels. |
| `frontend/src/types/index.ts` | Single file for all TypeScript interfaces. New scorecard types go here. |
| `frontend/src/components/common/Header.tsx` | Nav links use a hardcoded array `['/', '/projects', '/representatives']` with a parallel `labels` array. Adding `/scorecard` requires adding to both arrays in the same index position. |
| `frontend/src/App.tsx` | Header is currently commented out (`{/* <Header /> */}`). The scorecard route should still be added — if Header is enabled later, the nav link will appear. Check with the team whether to uncomment Header as part of this work. |
| `frontend/src/utils/config.ts` | Exports `appConfig` with `name` and `description`. Add `scorecardGroupId: import.meta.env.VITE_SCORECARD_GROUP_ID ?? ''` here. |

### Existing Patterns

**Import script pattern** (from `import_adu_project_data.py`):
```python
async def import_foo():
    service = get_cached_foo_service()
    ...

if __name__ == "__main__":
    asyncio.run(import_foo())
```

**DataSource pattern** (from `chicago_alderpersons.py`):
```python
class FooDataSource(DataSource):
    async def fetch_data(self) -> list[dict]: ...
    def get_source_info(self) -> dict: ...
```
The Legistar client does NOT follow this pattern — see decision rationale in plan.md.

**Route pattern** (from `entities.py`, `projects.py`):
```python
router = APIRouter()

@router.get("/", response_model=SomeModel)
async def list_things(
    service: SomeService = Depends(get_some_service),
):
    return await service.list_things()
```

**Service factory pattern** (from `service_factory.py`):
```python
def create_foo_service(provider=None) -> FooService:
    return FooService(provider=provider or get_foo_provider())

def get_foo_service(provider=Depends(get_foo_provider)) -> FooService:
    return FooService(provider=provider)
```

### Dependencies

**Internal:**
- `app.db.base.DatabaseProvider` — all providers implement this interface
- `app.db.dependencies` — `get_projects_provider()`, `get_entities_provider()`, `get_status_records_provider()`, `get_districts_provider()`
- `app.models.pydantic.models` — `Entity`, `EntityStatus`, `ProjectBase`, `DashboardConfig`
- `app.services.{project,entity,status}_service` — reused directly in the scorecard service

**External:**
- `aiohttp` — already in `pyproject.toml` (used by `chicago_alderpersons.py`). No new dependencies.
- Legistar Web API: `https://webapi.legistar.com/v1/chicago` — public, unauthenticated, OData 3.0

---

## Design Trade-offs

### Entity Name Matching

**Problem:** Legistar stores names differently than the Chicago data portal. Examples:
- Chicago API: `"Maria Hadden"` — Legistar: `"Ald. Maria Hadden"` or `"Hadden, Maria"`
- Need to handle: titles (Ald., Alderperson), comma-reversed order, suffixes (Jr., Sr., II), extra whitespace

**Options:**
1. Exact match — fast, breaks on any formatting difference
2. Lowercase + strip — catches case/whitespace, misses titles and commas
3. Full normalization (lowercase, strip, remove punctuation, sort tokens) — most robust
4. fuzzy matching (Levenshtein distance) — handles typos, but introduces false positives and adds a dependency

**Chosen:** Option 3 (full normalization). The risk of false positives with option 4 outweighs the benefit given that name inconsistencies follow predictable patterns (titles, commas). If normalization still fails for some names, the warning log will identify them for manual review.

**Implementation:** A pure `normalize_name(name: str) -> str` function in `legistar.py`. Applied to both sides of the comparison. Logged mismatches include both raw names for debugging.

### Scorecard Endpoint Query Strategy

**Problem:** Fetching a scorecard for 50 alderpersons × 8 projects naively produces N+1 queries.

**Current `list_status_records()` in StatusService:**
```python
# Existing: can filter by project_id OR entity_id, not both lists at once
await self.status_records_provider.filter_multiple(
    filters={"project_id": project_id},
    in_filters={"entity_id": entity_ids}
)
```

**For the scorecard:** We need all status records where `project_id IN [p1, p2, ..., p8] AND entity_id IN [e1, ..., e50]`. The existing `filter_multiple()` on `DatabaseProvider` supports `in_filters` for one field at a time, with exact match for others. This means we can call it with `in_filters={"project_id": project_ids, "entity_id": entity_ids}` — but only if `filter_multiple` supports multiple `in_filters` keys simultaneously.

**Check needed:** Look at `backend/app/db/sql.py` to confirm whether `filter_multiple()` accepts multiple keys in `in_filters`. If not, use a loop over project IDs (8 queries instead of 1), which is acceptable given 8 is a small fixed number.

**Alternatively:** Fetch all status records for the group's projects in one call using `in_filters={"project_id": project_ids}`, then filter by entity_id in Python. This is always safe regardless of `filter_multiple` implementation details.

**Chosen:** Fetch by `in_filters={"project_id": project_ids}` then filter entity_ids in Python. Avoids any assumptions about multi-key `in_filters` support.

### Frontend: Scorecard Table vs. Separate Component File

**Decision:** Put the table markup directly in `Scorecard.tsx` rather than extracting a `ScorecardTable.tsx` component.

**Rationale:** The table is not reused elsewhere. Extracting it now adds a prop-threading layer with no current benefit. If the table needs to be embedded in a different context later, extraction is straightforward. Follow YAGNI.

### Frontend: Group ID Resolution

**Options:**
1. `VITE_SCORECARD_GROUP_ID` env var — explicit, deployment-configurable
2. Fetch groups list and find by name — extra HTTP call, fragile if group name changes
3. Hardcode UUID in source — not configurable across deployments

**Chosen:** Option 1. The `appConfig` pattern in `src/utils/config.ts` is already the right place for this. Add `scorecardGroupId: import.meta.env.VITE_SCORECARD_GROUP_ID ?? ''` there.

If `VITE_SCORECARD_GROUP_ID` is empty, the scorecard page should display a clear error rather than making an API call with an empty string (which returns 422).

---

## Implementation Gotchas

### 1. Header nav is currently commented out in App.tsx

`App.tsx` line 32: `{/* <Header /> */}`. The nav link changes to `Header.tsx` are still correct to make, but the Scorecard link won't be visible in the app until the Header is re-enabled. Consider whether to uncomment `<Header />` as part of this work or leave it for a separate decision.

### 2. `create_project()` has no slug uniqueness guard

If the import script is run twice without the idempotency check, it will create duplicate projects with identical slugs. The `projects_provider.filter(slug=...)` check in `get_project_by_slug()` shows that slug filtering is supported. The script must call `get_project_by_slug(slug)` first and skip `create_project()` if a result is returned.

### 3. Legistar API pagination

The Legistar OData API returns at most 1000 records per request. For the `/matters` filter query and `/matters/{id}/sponsors`, this is not a concern (results will be small). For `/matters/{id}/histories` and `/eventitems/{id}/votes`, the results are also bounded by the council (50 alderpersons). No pagination handling is needed for this use case.

### 4. Legistar "final passage" detection

The matter histories endpoint returns all procedural steps for a bill. The target step is identified by:
- `MatterHistoryRollCallFlag == 1` (it was a roll-call vote)
- `MatterHistoryActionName` contains "passage" (case-insensitive) — the exact text may be "Final Passage", "Adopt Final Passage", etc.

Test this against at least one known GUID before finalizing the detection logic. The ADU GUID `54028B60-C4FC-EE11-A1FE-001DD804AF4C` is a good candidate since it's known to have had a final passage vote.

### 5. Legistar vote values

Legistar uses `VoteValueName` strings that may vary. Confirmed values from Chicago Legistar include: "Yea", "Nay", "Absent", "Abstain". The mapping dict in `legistar.py` should use `.lower()` comparison to handle any capitalization variants.

### 6. mypy and aiohttp type stubs

`aiohttp` may require `types-aiohttp` for strict mypy. Check the existing mypy configuration in `backend/pyproject.toml` — if `chicago_alderpersons.py` already passes mypy without type errors, the same approach (likely `# type: ignore` or stub install) applies here. The project rules prohibit `# type: ignore`, so install the stubs if needed.

### 7. `district_id` in `EntityCreate` is not optional

`EntityCreate` inherits from `EntityBase` which has `district_id: UUID` as required. The `entity_importer.py` handles this by looking up the district. The Legistar client doesn't need to create entities — it only reads them. But be careful: when building `ScorecardEntityRow`, the `Entity` object from the DB will have `district_id` populated, so `district_name` enrichment is needed. The `ScorecardService` must call `_enrich_with_district_names()` or equivalent batch fetch.

### 8. Mypy strict typing for `ScorecardResponse`

The `statuses` field on `ScorecardEntityRow` is `dict[str, ScorecardEntityStatus]` keyed by project ID as string. mypy will enforce this. In the service, when building this dict, use `str(project.id)` consistently as the key.

---

## Future Considerations

- **Auto-refresh**: The scorecard import is currently a one-time script. If Legistar data changes (e.g., new sponsors added), the import must be re-run manually. A future enhancement could register `import_scorecard_projects` as a scheduled task via Railway cron.
- **Import via admin UI**: The `DataImportPage.tsx` admin page already supports triggering imports via the API. A future enhancement could expose the scorecard import as an admin-triggerable action via `GET /api/imports/scorecard`.
- **Project ordering**: The scorecard columns currently appear in the order returned by `list_projects()`. A future enhancement could add an `order` field to `Project` or `DashboardConfig` to control column ordering on the scorecard.
- **Filtering by issue type**: The scorecard plan mentions grouping vote vs. sponsorship projects. A future filter control on the scorecard page could show/hide project columns by type. This would require a `project_category` field or tag system.
- **NWPO and Green Social Housing**: Excluded for now per `scorecard.md`. If added later, they follow the same sponsorship import path as Single Stair and CHA Housing.
