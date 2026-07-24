"""Unit tests for ScorecardService and scorecard import helpers."""

from uuid import uuid4

import pytest

from app.imports.sources.chicago_city_clerk_elms import normalize_name
from app.models.pydantic.models import (
    DashboardConfig,
    EntityStatus,
    MetricDisplayConfig,
)
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


class TestGetScorecardUnknownExcludedFromDenominator:
    @pytest.mark.asyncio
    async def test_unknown_status_excluded_from_total_scoreable(self):
        """UNKNOWN (not in office) must not count toward total_scoreable."""
        group_id = uuid4()
        jurisdiction_id = uuid4()

        p_vote = make_project(
            group_id=group_id,
            jurisdiction_id=jurisdiction_id,
            preferred_status=EntityStatus.SOLID_APPROVAL,
        )
        p_other = make_project(
            group_id=group_id,
            jurisdiction_id=jurisdiction_id,
            preferred_status=EntityStatus.SOLID_APPROVAL,
        )
        entity = make_entity(jurisdiction_id=jurisdiction_id)

        # Entity was not in office for p_vote (UNKNOWN), aligned on p_other
        sr_vote = make_status_record(
            entity_id=entity.id,
            project_id=p_vote.id,
            status=EntityStatus.UNKNOWN,
        )
        sr_other = make_status_record(
            entity_id=entity.id,
            project_id=p_other.id,
            status=EntityStatus.SOLID_APPROVAL,
        )

        service = _build_scorecard_service(
            projects_data=[p_vote, p_other],
            entities_data=[entity],
            status_records_data=[sr_vote, sr_other],
        )
        result = await service.get_scorecard(group_id, "Test Group")

        row = result.entities[0]
        # Only p_other counts toward denominator (p_vote is UNKNOWN = not in office)
        assert row.total_scoreable == 1
        assert row.aligned_count == 1


class TestGetScorecardMetrics:
    """Metric descriptors + per-entity values threaded through the scorecard."""

    @staticmethod
    def _metrics(*keys: str) -> list[MetricDisplayConfig]:
        return [
            MetricDisplayConfig(key=k, label=k.replace("_", " ").title()) for k in keys
        ]

    @pytest.mark.asyncio
    async def test_metrics_config_from_first_project_with_metrics(self):
        """Config comes from the first project in position order that declares metrics."""
        group_id = uuid4()
        jurisdiction_id = uuid4()

        p_first = make_project(
            group_id=group_id,
            jurisdiction_id=jurisdiction_id,
            dashboard_config=DashboardConfig(position=0),
        )
        p_second = make_project(
            group_id=group_id,
            jurisdiction_id=jurisdiction_id,
            dashboard_config=DashboardConfig(
                position=1, metrics=self._metrics("zoning_median_days")
            ),
        )
        p_third = make_project(
            group_id=group_id,
            jurisdiction_id=jurisdiction_id,
            dashboard_config=DashboardConfig(
                position=2, metrics=self._metrics("something_else")
            ),
        )

        # Seeded out of position order to prove sorting drives the choice.
        service = _build_scorecard_service(projects_data=[p_third, p_second, p_first])
        result = await service.get_scorecard(group_id, "Test Group")

        assert [m.key for m in result.metrics] == ["zoning_median_days"]

    @pytest.mark.asyncio
    async def test_undeclared_metadata_keys_are_dropped(self):
        """Only keys declared in the metrics config surface on the row."""
        group_id = uuid4()
        jurisdiction_id = uuid4()

        project = make_project(
            group_id=group_id,
            jurisdiction_id=jurisdiction_id,
            dashboard_config=DashboardConfig(
                position=0, metrics=self._metrics("bonus_units")
            ),
        )
        entity = make_entity(jurisdiction_id=jurisdiction_id)
        record = make_status_record(
            entity_id=entity.id,
            project_id=project.id,
            status=EntityStatus.SOLID_APPROVAL,
            record_metadata={"bonus_units": 42, "internal_note": "not for display"},
        )

        service = _build_scorecard_service(
            projects_data=[project],
            entities_data=[entity],
            status_records_data=[record],
        )
        result = await service.get_scorecard(group_id, "Test Group")

        assert result.entities[0].metrics == {"bonus_units": 42}

    @pytest.mark.asyncio
    async def test_lowest_position_project_wins_key_conflicts(self):
        """When two projects carry the same metric key, the earlier project wins."""
        group_id = uuid4()
        jurisdiction_id = uuid4()

        p_first = make_project(
            group_id=group_id,
            jurisdiction_id=jurisdiction_id,
            dashboard_config=DashboardConfig(
                position=0, metrics=self._metrics("bonus_units")
            ),
        )
        p_second = make_project(
            group_id=group_id,
            jurisdiction_id=jurisdiction_id,
            dashboard_config=DashboardConfig(position=1),
        )
        entity = make_entity(jurisdiction_id=jurisdiction_id)
        sr_second = make_status_record(
            entity_id=entity.id,
            project_id=p_second.id,
            status=EntityStatus.NEUTRAL,
            record_metadata={"bonus_units": 999},
        )
        sr_first = make_status_record(
            entity_id=entity.id,
            project_id=p_first.id,
            status=EntityStatus.NEUTRAL,
            record_metadata={"bonus_units": 1},
        )

        service = _build_scorecard_service(
            projects_data=[p_first, p_second],
            entities_data=[entity],
            status_records_data=[sr_second, sr_first],
        )
        result = await service.get_scorecard(group_id, "Test Group")

        assert result.entities[0].metrics == {"bonus_units": 1}

    @pytest.mark.asyncio
    async def test_entity_without_records_has_none_metrics(self):
        """An entity with no status records gets metrics=None, not an empty dict."""
        group_id = uuid4()
        jurisdiction_id = uuid4()

        project = make_project(
            group_id=group_id,
            jurisdiction_id=jurisdiction_id,
            dashboard_config=DashboardConfig(
                position=0, metrics=self._metrics("bonus_units")
            ),
        )
        with_record = make_entity(jurisdiction_id=jurisdiction_id, name="Has Record")
        without_record = make_entity(jurisdiction_id=jurisdiction_id, name="No Record")
        record = make_status_record(
            entity_id=with_record.id,
            project_id=project.id,
            status=EntityStatus.SOLID_APPROVAL,
            record_metadata={"bonus_units": 7},
        )

        service = _build_scorecard_service(
            projects_data=[project],
            entities_data=[with_record, without_record],
            status_records_data=[record],
        )
        result = await service.get_scorecard(group_id, "Test Group")

        by_name = {row.entity.name: row for row in result.entities}
        assert by_name["Has Record"].metrics == {"bonus_units": 7}
        assert by_name["No Record"].metrics is None

    @pytest.mark.asyncio
    async def test_record_with_only_undeclared_keys_yields_none(self):
        """Metadata that contributes no declared key leaves metrics as None."""
        group_id = uuid4()
        jurisdiction_id = uuid4()

        project = make_project(
            group_id=group_id,
            jurisdiction_id=jurisdiction_id,
            dashboard_config=DashboardConfig(
                position=0, metrics=self._metrics("bonus_units")
            ),
        )
        entity = make_entity(jurisdiction_id=jurisdiction_id)
        record = make_status_record(
            entity_id=entity.id,
            project_id=project.id,
            status=EntityStatus.SOLID_APPROVAL,
            record_metadata={"unrelated": 1},
        )

        service = _build_scorecard_service(
            projects_data=[project],
            entities_data=[entity],
            status_records_data=[record],
        )
        result = await service.get_scorecard(group_id, "Test Group")

        assert result.entities[0].metrics is None

    @pytest.mark.asyncio
    async def test_no_metrics_config_anywhere(self):
        """Without any metrics config the response carries [] and rows stay metric-free."""
        group_id = uuid4()
        jurisdiction_id = uuid4()

        project = make_project(group_id=group_id, jurisdiction_id=jurisdiction_id)
        entity = make_entity(jurisdiction_id=jurisdiction_id)
        record = make_status_record(
            entity_id=entity.id,
            project_id=project.id,
            status=EntityStatus.SOLID_APPROVAL,
            record_metadata={"bonus_units": 42},
        )

        service = _build_scorecard_service(
            projects_data=[project],
            entities_data=[entity],
            status_records_data=[record],
        )
        result = await service.get_scorecard(group_id, "Test Group")

        assert result.metrics == []
        assert result.entities[0].metrics is None

    @pytest.mark.asyncio
    async def test_scores_identical_with_and_without_metrics_config(self):
        """Adding metrics config must not perturb aligned_count/total_scoreable."""
        group_id = uuid4()
        jurisdiction_id = uuid4()
        metrics = self._metrics("bonus_units")

        def build(with_metrics: bool):
            p1 = make_project(
                id=uuid4(),
                group_id=group_id,
                jurisdiction_id=jurisdiction_id,
                preferred_status=EntityStatus.SOLID_APPROVAL,
                dashboard_config=DashboardConfig(
                    position=0, metrics=metrics if with_metrics else None
                ),
            )
            p2 = make_project(
                group_id=group_id,
                jurisdiction_id=jurisdiction_id,
                preferred_status=EntityStatus.SOLID_DISAPPROVAL,
                dashboard_config=DashboardConfig(position=1),
            )
            p3 = make_project(
                group_id=group_id,
                jurisdiction_id=jurisdiction_id,
                preferred_status=EntityStatus.SOLID_APPROVAL,
                dashboard_config=DashboardConfig(position=2),
            )
            entity = make_entity(jurisdiction_id=jurisdiction_id)
            records = [
                make_status_record(
                    entity_id=entity.id,
                    project_id=p1.id,
                    status=EntityStatus.SOLID_APPROVAL,
                    record_metadata={"bonus_units": 42},
                ),
                make_status_record(
                    entity_id=entity.id,
                    project_id=p2.id,
                    status=EntityStatus.SOLID_DISAPPROVAL,
                ),
                make_status_record(
                    entity_id=entity.id,
                    project_id=p3.id,
                    status=EntityStatus.UNKNOWN,
                ),
            ]
            return _build_scorecard_service(
                projects_data=[p1, p2, p3],
                entities_data=[entity],
                status_records_data=records,
            )

        without = await build(False).get_scorecard(group_id, "Test Group")
        with_metrics = await build(True).get_scorecard(group_id, "Test Group")

        assert without.entities[0].metrics is None
        assert with_metrics.entities[0].metrics == {"bonus_units": 42}
        assert (
            with_metrics.entities[0].aligned_count == without.entities[0].aligned_count
        )
        assert (
            with_metrics.entities[0].total_scoreable
            == without.entities[0].total_scoreable
        )
        # Sanity: the scenario actually exercises scoring (approve +1, cosponsor -1, unknown skipped)
        assert without.entities[0].aligned_count == 0
        assert without.entities[0].total_scoreable == 2


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
