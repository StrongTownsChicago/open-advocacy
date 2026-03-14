"""Unit tests for ScorecardService and scorecard import helpers."""

from uuid import uuid4

import pytest

from app.imports.sources.chicago_city_clerk_elms import normalize_name
from app.models.pydantic.models import DashboardConfig, EntityStatus
from app.services.scorecard_service import ScorecardService
from tests.factories import make_entity, make_project, make_status_record
from tests.mock_provider import MockDatabaseProvider


def _build_scorecard_service(
    projects_data=None,
    entities_data=None,
    status_records_data=None,
    districts_data=None,
) -> ScorecardService:
    """Build a ScorecardService with seeded MockDatabaseProviders."""
    projects_provider = MockDatabaseProvider()
    entities_provider = MockDatabaseProvider()
    status_records_provider = MockDatabaseProvider()
    districts_provider = MockDatabaseProvider()

    for obj in projects_data or []:
        projects_provider.seed(obj)
    for obj in entities_data or []:
        entities_provider.seed(obj)
    for obj in status_records_data or []:
        status_records_provider.seed(obj)
    for obj in districts_data or []:
        districts_provider.seed(obj)

    return ScorecardService(
        projects_provider=projects_provider,
        entities_provider=entities_provider,
        status_records_provider=status_records_provider,
        districts_provider=districts_provider,
    )


class TestGetScorecardReturnsCorrectProjectCount:
    @pytest.mark.asyncio
    async def test_only_projects_for_group_are_returned(self):
        """Projects from a different group must not appear in the scorecard."""
        group_id = uuid4()
        other_group_id = uuid4()
        jurisdiction_id = uuid4()

        p1 = make_project(group_id=group_id, jurisdiction_id=jurisdiction_id)
        p2 = make_project(group_id=group_id, jurisdiction_id=jurisdiction_id)
        p3 = make_project(group_id=other_group_id, jurisdiction_id=jurisdiction_id)

        service = _build_scorecard_service(projects_data=[p1, p2, p3])
        result = await service.get_scorecard(group_id, "Test Group")

        assert len(result.projects) == 2
        project_ids = {str(sp.id) for sp in result.projects}
        assert str(p3.id) not in project_ids


class TestGetScorecardAlignmentScore:
    @pytest.mark.asyncio
    async def test_alignment_score_computed_correctly(self):
        """aligned_count should count only projects where entity status == preferred_status."""
        group_id = uuid4()
        jurisdiction_id = uuid4()

        p1 = make_project(
            group_id=group_id,
            jurisdiction_id=jurisdiction_id,
            preferred_status=EntityStatus.SOLID_APPROVAL,
        )
        p2 = make_project(
            group_id=group_id,
            jurisdiction_id=jurisdiction_id,
            preferred_status=EntityStatus.SOLID_APPROVAL,
        )
        entity = make_entity(jurisdiction_id=jurisdiction_id)

        # Entity aligns on p1 (SOLID_APPROVAL == preferred_status) but not p2
        sr1 = make_status_record(
            entity_id=entity.id,
            project_id=p1.id,
            status=EntityStatus.SOLID_APPROVAL,
        )
        sr2 = make_status_record(
            entity_id=entity.id,
            project_id=p2.id,
            status=EntityStatus.SOLID_DISAPPROVAL,
        )

        service = _build_scorecard_service(
            projects_data=[p1, p2],
            entities_data=[entity],
            status_records_data=[sr1, sr2],
        )
        result = await service.get_scorecard(group_id, "Test Group")

        assert len(result.entities) == 1
        row = result.entities[0]
        assert row.aligned_count == 1
        assert row.total_scoreable == 2


class TestGetScorecardEntityWithNoStatusRecord:
    @pytest.mark.asyncio
    async def test_entity_without_status_record_gets_unknown(self):
        """Entities with no status records should appear with UNKNOWN status."""
        group_id = uuid4()
        jurisdiction_id = uuid4()

        project = make_project(
            group_id=group_id,
            jurisdiction_id=jurisdiction_id,
            preferred_status=EntityStatus.SOLID_APPROVAL,
        )
        entity = make_entity(jurisdiction_id=jurisdiction_id)

        service = _build_scorecard_service(
            projects_data=[project],
            entities_data=[entity],
            status_records_data=[],  # No records
        )
        result = await service.get_scorecard(group_id, "Test Group")

        assert len(result.entities) == 1
        row = result.entities[0]
        status_entry = row.statuses[str(project.id)]
        assert status_entry.status == EntityStatus.UNKNOWN
        assert row.aligned_count == 0


class TestGetScorecardStatusLabelResolution:
    @pytest.mark.asyncio
    async def test_resolves_label_from_project_config(self):
        """Status label should come from project's status_labels config."""
        group_id = uuid4()
        jurisdiction_id = uuid4()

        project = make_project(
            group_id=group_id,
            jurisdiction_id=jurisdiction_id,
            preferred_status=EntityStatus.SOLID_APPROVAL,
            dashboard_config=DashboardConfig(
                status_labels={"solid_approval": "Voted Yes", "unknown": "Absent"}
            ),
        )
        entity = make_entity(jurisdiction_id=jurisdiction_id)
        sr = make_status_record(
            entity_id=entity.id,
            project_id=project.id,
            status=EntityStatus.SOLID_APPROVAL,
        )

        service = _build_scorecard_service(
            projects_data=[project],
            entities_data=[entity],
            status_records_data=[sr],
        )
        result = await service.get_scorecard(group_id, "Test Group")

        row = result.entities[0]
        assert row.statuses[str(project.id)].label == "Voted Yes"

    @pytest.mark.asyncio
    async def test_falls_back_to_default_label_when_no_config(self):
        """When project has no status_labels, use the default label."""
        group_id = uuid4()
        jurisdiction_id = uuid4()

        project = make_project(
            group_id=group_id,
            jurisdiction_id=jurisdiction_id,
            preferred_status=EntityStatus.SOLID_APPROVAL,
            dashboard_config=None,
        )
        entity = make_entity(jurisdiction_id=jurisdiction_id)
        sr = make_status_record(
            entity_id=entity.id,
            project_id=project.id,
            status=EntityStatus.SOLID_APPROVAL,
        )

        service = _build_scorecard_service(
            projects_data=[project],
            entities_data=[entity],
            status_records_data=[sr],
        )
        result = await service.get_scorecard(group_id, "Test Group")

        row = result.entities[0]
        assert row.statuses[str(project.id)].label == "Solid Approval"


class TestGetScorecardReturnsEmptyWhenNoProjects:
    @pytest.mark.asyncio
    async def test_returns_empty_response_when_group_has_no_projects(self):
        """Empty projects list should return an empty ScorecardResponse without error."""
        group_id = uuid4()
        service = _build_scorecard_service()
        result = await service.get_scorecard(group_id, "Test Group")

        assert result.projects == []
        assert result.entities == []


class TestGetScorecardEntityRowsContainAllProjects:
    @pytest.mark.asyncio
    async def test_every_entity_row_has_status_for_every_project(self):
        """Every entity row must have a status entry for every project (fill gaps with UNKNOWN)."""
        group_id = uuid4()
        jurisdiction_id = uuid4()

        p1 = make_project(group_id=group_id, jurisdiction_id=jurisdiction_id)
        p2 = make_project(group_id=group_id, jurisdiction_id=jurisdiction_id)
        p3 = make_project(group_id=group_id, jurisdiction_id=jurisdiction_id)

        e1 = make_entity(jurisdiction_id=jurisdiction_id)
        e2 = make_entity(jurisdiction_id=jurisdiction_id)

        # Only one record: e1 on p1
        sr = make_status_record(
            entity_id=e1.id, project_id=p1.id, status=EntityStatus.SOLID_APPROVAL
        )

        service = _build_scorecard_service(
            projects_data=[p1, p2, p3],
            entities_data=[e1, e2],
            status_records_data=[sr],
        )
        result = await service.get_scorecard(group_id, "Test Group")

        assert len(result.entities) == 2
        for row in result.entities:
            assert len(row.statuses) == 3


class TestNormalizeNameEdgeCases:
    def test_middle_initial_stripped_comma_reversed(self):
        """Middle initial is stripped from comma-reversed ELMS names so they match DB entity names.

        ELMS returns "Lee, Nicole T." but the DB stores "Nicole Lee" — both must
        normalize to "nicole lee" for the cache lookup to match.
        """
        assert normalize_name("Lee, Nicole T.") == "nicole lee"
        assert normalize_name("Nicole Lee") == "nicole lee"

    def test_hyphenated_name_loses_hyphen(self):
        """Hyphenated names collapse to a single token after punctuation removal.

        "Ramirez-Rosa" → "ramirezrosa" (hyphen stripped). Both the DB entity name
        and the ELMS name must go through normalize_name to produce the same key;
        a DB entry stored as "Carlos Ramirez-Rosa" will match the cache key
        "carlos ramirezrosa" correctly.
        """
        assert normalize_name("Ramirez-Rosa, Carlos") == "carlos ramirezrosa"
        assert normalize_name("Carlos Ramirez-Rosa") == "carlos ramirezrosa"
