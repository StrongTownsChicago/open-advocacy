# Test Plan: Multi-Issue Scorecard

## Test Coverage Strategy

The scorecard feature introduces three new testable units:
1. `LegistarClient` — async HTTP client with name normalization logic
2. `ScorecardService` — alignment score computation, status label resolution
3. `GET /api/scorecard` route — auth enforcement, parameter validation, response shape

All backend tests use the existing `MockDatabaseProvider` from `tests/mock_provider.py` and `pytest-asyncio`. No real HTTP calls are made in tests.

---

### Unit Tests

#### `backend/tests/test_legistar_client.py`

Tests that mock `aiohttp.ClientSession` using `unittest.mock.AsyncMock` / `pytest-aiohttp` or `aioresponses`.

```python
# test_get_matter_id_found
# Tests: correct numeric MatterId extracted from OData response
# Setup: mock GET /matters?$filter=... returns [{"MatterId": 12345, "MatterGuid": "..."}]
# Assert: returns 12345

# test_get_matter_id_not_found
# Tests: None returned when OData response is empty list
# Setup: mock GET /matters returns []
# Assert: returns None

# test_get_matter_id_http_error
# Tests: exception raised on non-200 response
# Setup: mock GET /matters returns 500
# Assert: raises exception (aiohttp.ClientError or custom)

# test_get_matter_votes_finds_final_passage
# Tests: correct EventItemId used to fetch votes
# Setup:
#   - mock GET /matters/{id}/histories returns [
#       {"MatterHistoryRollCallFlag": 1, "MatterHistoryActionName": "Final Passage", "MatterHistoryEventItemId": 99},
#       {"MatterHistoryRollCallFlag": 0, "MatterHistoryActionName": "Referred", "MatterHistoryEventItemId": 88},
#     ]
#   - mock GET /eventitems/99/votes returns [{...}]
# Assert: returns list from eventitems/99 (not 88)

# test_get_matter_votes_returns_none_when_no_final_passage
# Tests: None returned when no roll-call history exists
# Setup: mock histories returns records with RollCallFlag=0 only
# Assert: returns None

# test_get_matter_votes_case_insensitive_action_name
# Tests: "final passage" match is case-insensitive
# Setup: history record with MatterHistoryActionName = "ADOPT FINAL PASSAGE"
# Assert: correctly identified as final passage event

# test_get_matter_sponsors_returns_list
# Tests: sponsor list returned correctly
# Setup: mock GET /matters/{id}/sponsors returns [{MatterSponsorName: "Maria Hadden", MatterSponsorSequence: 1}]
# Assert: list of dicts returned as-is

# test_normalize_name_removes_title_prefix
# Tests: pure function — no mocking
# "Ald. Maria Hadden" → "maria hadden"

# test_normalize_name_handles_comma_reversed
# "HADDEN, MARIA" → "hadden maria"

# test_normalize_name_collapses_whitespace
# "  Carlos   Ramirez-Rosa  " → "carlos ramirezrosa" (or equivalent normalized form)

# test_normalize_name_handles_suffix
# "Walter Burnett Jr." → "walter burnett jr"

# test_vote_value_to_entity_status_mapping
# Tests: all known vote value strings map to correct EntityStatus
# Pure function test — no mocking needed
# "Yea" → SOLID_APPROVAL
# "Nay" → SOLID_DISAPPROVAL
# "Abstain" → NEUTRAL
# "Recuse" → NEUTRAL
# "Absent" → UNKNOWN
# "Not Voting" → UNKNOWN
# "UNKNOWN_VALUE" → UNKNOWN (default case)
```

#### `backend/tests/test_scorecard_service.py`

Uses `MockDatabaseProvider` seeded with test data.

```python
# test_get_scorecard_returns_correct_project_count
# Tests: all projects for the group are returned in the response
# Setup: seed 3 projects with matching group_id, 1 project with different group_id
# Assert: ScorecardResponse.projects has length 3

# test_get_scorecard_computes_alignment_score_correctly
# Tests: aligned_count counts only projects where entity status == preferred_status
# Setup:
#   - 2 projects with preferred_status=SOLID_APPROVAL
#   - 1 entity with SOLID_APPROVAL on project 1, SOLID_DISAPPROVAL on project 2
# Assert: entity row has aligned_count=1, total_scoreable=2

# test_get_scorecard_entity_without_status_record_gets_unknown
# Tests: entities missing status records default to UNKNOWN, not excluded
# Setup: 1 project, 1 entity, no status records
# Assert: entity row has statuses[project_id].status == UNKNOWN, aligned_count=0

# test_get_scorecard_resolves_status_label_from_project_config
# Tests: label in ScorecardEntityStatus uses project's status_labels if available
# Setup: project with status_labels={"solid_approval": "Voted Yes"}, entity with SOLID_APPROVAL
# Assert: statuses[project_id].label == "Voted Yes"

# test_get_scorecard_falls_back_to_default_label_when_no_config
# Tests: label falls back to getStatusLabel() when project has no status_labels
# Setup: project with no DashboardConfig, entity with SOLID_APPROVAL
# Assert: statuses[project_id].label == "Solid Approval" (default)

# test_get_scorecard_returns_empty_when_no_projects
# Tests: empty response (not an error) when group has no projects
# Setup: group_id exists but no projects linked to it
# Assert: ScorecardResponse(projects=[], entities=[])

# test_get_scorecard_entity_rows_contain_all_projects
# Tests: every entity row has status entries for every project (including UNKNOWN)
# Setup: 3 projects, 2 entities, status records for only some combinations
# Assert: each entity's statuses dict has 3 keys regardless of which records exist
```

#### `backend/tests/test_api_scorecard.py`

```python
# test_scorecard_endpoint_requires_no_auth
# Tests: GET /api/scorecard?group_id={uuid} returns 200 without Authorization header
# Setup: override get_scorecard_service with mock returning empty ScorecardResponse

# test_scorecard_endpoint_missing_group_id_returns_422
# Tests: GET /api/scorecard without group_id query param returns 422 (FastAPI validation)

# test_scorecard_endpoint_invalid_group_id_format_returns_422
# Tests: GET /api/scorecard?group_id=not-a-uuid returns 422

# test_scorecard_endpoint_response_shape
# Tests: response body has "projects" and "entities" keys
# Setup: mock service returns ScorecardResponse with 1 project and 1 entity row
# Assert: response JSON has correct keys and nested structure
```

---

### Frontend Unit Tests

#### `frontend/src/pages/Scorecard.test.tsx`

Uses Vitest + React Testing Library. Mock `scorecardService.getScorecard` with `vi.mock`.

```typescript
// test: renders loading spinner before data arrives
// Setup: mock returns a promise that never resolves
// Assert: CircularProgress is in the document

// test: renders error message when API call fails
// Setup: mock rejects with an error
// Assert: error text is visible (check ErrorDisplay component renders)

// test: renders table headers for each project
// Setup: mock returns ScorecardResponse with 2 projects ("ADU Vote", "No Parking Vote")
// Assert: "ADU Vote" and "No Parking Vote" text in document

// test: renders entity name in table row
// Setup: mock returns 1 entity row with entity.name = "Maria Hadden"
// Assert: "Maria Hadden" text in document

// test: renders alignment score as "X / Y" format
// Setup: entity row with aligned_count=3, total_scoreable=8
// Assert: "3 / 8" text in document

// test: entity name links to representative detail page
// Setup: entity with id="abc-123"
// Assert: link with href="/representatives/abc-123" in document

// test: renders empty state when no entities returned
// Setup: mock returns ScorecardResponse with empty entities array
// Assert: some "no data" message visible (not a crash)

// test: sort by alignment score re-orders rows
// Setup: mock returns 2 entities — first with aligned_count=2, second with aligned_count=5
// Assert: after clicking sort control, entity with count=5 appears before count=2
```

---

### Edge Case Coverage

| Edge Case | Test Location | Covered |
|---|---|---|
| Legistar GUID not found (empty OData response) | `test_legistar_client.py::test_get_matter_id_not_found` | [ ] |
| Legistar HTTP 5xx error | `test_legistar_client.py::test_get_matter_id_http_error` | [ ] |
| No final passage vote in histories | `test_legistar_client.py::test_get_matter_votes_returns_none_when_no_final_passage` | [ ] |
| Vote value not in known set | `test_legistar_client.py::test_vote_value_to_entity_status_mapping` | [ ] |
| Name normalization edge cases (titles, commas, suffixes) | `test_legistar_client.py::test_normalize_name_*` | [ ] |
| Entity with no status record → UNKNOWN | `test_scorecard_service.py::test_get_scorecard_entity_without_status_record_gets_unknown` | [ ] |
| Group with no projects → empty response | `test_scorecard_service.py::test_get_scorecard_returns_empty_when_no_projects` | [ ] |
| Alignment score computation | `test_scorecard_service.py::test_get_scorecard_computes_alignment_score_correctly` | [ ] |
| Status label from project config | `test_scorecard_service.py::test_get_scorecard_resolves_status_label_from_project_config` | [ ] |
| Missing `group_id` query param | `test_api_scorecard.py::test_scorecard_endpoint_missing_group_id_returns_422` | [ ] |
| Unauthenticated access (public endpoint) | `test_api_scorecard.py::test_scorecard_endpoint_requires_no_auth` | [ ] |
| Frontend: API failure → error display | `Scorecard.test.tsx::renders error message when API call fails` | [ ] |
| Frontend: empty entities list → no crash | `Scorecard.test.tsx::renders empty state when no entities returned` | [ ] |
| Frontend: sort behavior | `Scorecard.test.tsx::sort by alignment score re-orders rows` | [ ] |

---

## Test Data Requirements

### Backend test fixtures

The `MockDatabaseProvider` in `tests/mock_provider.py` and `tests/factories.py` already support creating projects and entities. Extend `factories.py` with:

```python
def make_scorecard_project(group_id=None, preferred_status=EntityStatus.SOLID_APPROVAL, **kwargs) -> Project:
    """Factory for projects with DashboardConfig status_labels."""
    ...

def make_entity_status_record(entity_id, project_id, status=EntityStatus.UNKNOWN) -> EntityStatusRecord:
    """Factory for status records."""
    ...
```

### Frontend test fixtures

```typescript
// src/pages/Scorecard.test.tsx — inline mock data
const mockScorecardResponse: ScorecardResponse = {
  projects: [
    {
      id: 'project-1',
      title: 'ADU Citywide Vote',
      slug: 'adu-citywide-vote',
      preferred_status: EntityStatus.SOLID_APPROVAL,
      status_labels: { solid_approval: 'Voted Yes', solid_disapproval: 'Voted No', unknown: 'Absent' },
    },
  ],
  entities: [
    {
      entity: { id: 'entity-1', name: 'Maria Hadden', entity_type: 'alderperson', district_name: 'Ward 49', jurisdiction_id: 'jur-1' },
      statuses: { 'project-1': { status: EntityStatus.SOLID_APPROVAL, label: 'Voted Yes' } },
      aligned_count: 1,
      total_scoreable: 1,
    },
  ],
};
```

---

## Success Metrics

- Backend unit test coverage for new files: all logic branches covered (aiming for 100% on pure functions, 90%+ on async service methods)
- All edge cases in the table above marked as covered before implementation is considered done
- No `# type: ignore` comments in new files
- `poetry run mypy .` passes on all new Python files
- `npm run type-check` passes on all new TypeScript files
- `poetry run pytest` green (no regressions in existing tests)
- `npm test` green (no regressions in existing tests)
