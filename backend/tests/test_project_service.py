"""Tests for ProjectService, focusing on calculate_status_distribution_with_unknowns."""

from uuid import uuid4

import pytest

from app.models.pydantic.models import (
    EntityStatus,
    ProjectBase,
    ProjectStatus,
)
from app.services.project_service import ProjectService
from tests.factories import (
    make_group,
    make_jurisdiction,
    make_project,
    make_status_record,
)
from tests.mock_provider import MockDatabaseProvider


class TestCalculateStatusDistributionWithUnknowns:
    """Tests for the pure-logic calculate_status_distribution_with_unknowns method."""

    def setup_method(self):
        self.service = ProjectService(
            projects_provider=MockDatabaseProvider(),
            status_records_provider=MockDatabaseProvider(),
            entities_provider=MockDatabaseProvider(),
            jurisdictions_provider=MockDatabaseProvider(),
            groups_provider=MockDatabaseProvider(),
        )

    def test_empty_records_all_unknown(self):
        """With no status records, all entities should be unknown."""
        result = self.service.calculate_status_distribution_with_unknowns([], 10)
        assert result.total == 10
        assert result.unknown == 10
        assert result.solid_approval == 0
        assert result.leaning_approval == 0
        assert result.neutral == 0
        assert result.leaning_disapproval == 0
        assert result.solid_disapproval == 0

    def test_zero_entities(self):
        """With zero total entities, distribution should be all zeros."""
        result = self.service.calculate_status_distribution_with_unknowns([], 0)
        assert result.total == 0
        assert result.unknown == 0

    def test_all_statuses_represented(self):
        """Each status type should be counted correctly."""
        project_id = uuid4()
        records = [
            make_status_record(
                entity_id=uuid4(),
                project_id=project_id,
                status=EntityStatus.SOLID_APPROVAL,
            ),
            make_status_record(
                entity_id=uuid4(),
                project_id=project_id,
                status=EntityStatus.LEANING_APPROVAL,
            ),
            make_status_record(
                entity_id=uuid4(), project_id=project_id, status=EntityStatus.NEUTRAL
            ),
            make_status_record(
                entity_id=uuid4(),
                project_id=project_id,
                status=EntityStatus.LEANING_DISAPPROVAL,
            ),
            make_status_record(
                entity_id=uuid4(),
                project_id=project_id,
                status=EntityStatus.SOLID_DISAPPROVAL,
            ),
        ]
        result = self.service.calculate_status_distribution_with_unknowns(records, 8)
        assert result.total == 8
        assert result.solid_approval == 1
        assert result.leaning_approval == 1
        assert result.neutral == 1
        assert result.leaning_disapproval == 1
        assert result.solid_disapproval == 1
        assert result.unknown == 3  # 8 - 5 = 3

    def test_partial_coverage(self):
        """Only some entities have status records; rest are unknown."""
        project_id = uuid4()
        records = [
            make_status_record(
                entity_id=uuid4(),
                project_id=project_id,
                status=EntityStatus.SOLID_APPROVAL,
            ),
            make_status_record(
                entity_id=uuid4(),
                project_id=project_id,
                status=EntityStatus.SOLID_APPROVAL,
            ),
        ]
        result = self.service.calculate_status_distribution_with_unknowns(records, 5)
        assert result.total == 5
        assert result.solid_approval == 2
        assert result.unknown == 3

    def test_duplicate_entity_ids_deduped(self):
        """Multiple records for the same entity should be deduped (last wins)."""
        project_id = uuid4()
        entity_id = uuid4()
        records = [
            make_status_record(
                entity_id=entity_id, project_id=project_id, status=EntityStatus.NEUTRAL
            ),
            make_status_record(
                entity_id=entity_id,
                project_id=project_id,
                status=EntityStatus.SOLID_APPROVAL,
            ),
        ]
        result = self.service.calculate_status_distribution_with_unknowns(records, 3)
        assert result.total == 3
        # Only one entity counted (deduped), so unknown = 3 - 1 = 2
        assert result.unknown == 2
        # The exact status depends on dict iteration, but total non-unknown should be 1
        non_unknown = (
            result.solid_approval
            + result.leaning_approval
            + result.neutral
            + result.leaning_disapproval
            + result.solid_disapproval
        )
        assert non_unknown == 1

    def test_unknown_status_records_stay_unknown(self):
        """Records with UNKNOWN status should not decrement the unknown count."""
        project_id = uuid4()
        records = [
            make_status_record(
                entity_id=uuid4(), project_id=project_id, status=EntityStatus.UNKNOWN
            ),
        ]
        result = self.service.calculate_status_distribution_with_unknowns(records, 5)
        assert result.total == 5
        assert result.unknown == 5  # The UNKNOWN record re-increments after decrement

    def test_all_entities_have_status(self):
        """When all entities have explicit non-unknown status, unknown should be 0."""
        project_id = uuid4()
        records = [
            make_status_record(
                entity_id=uuid4(),
                project_id=project_id,
                status=EntityStatus.SOLID_APPROVAL,
            ),
            make_status_record(
                entity_id=uuid4(),
                project_id=project_id,
                status=EntityStatus.LEANING_DISAPPROVAL,
            ),
            make_status_record(
                entity_id=uuid4(), project_id=project_id, status=EntityStatus.NEUTRAL
            ),
        ]
        result = self.service.calculate_status_distribution_with_unknowns(records, 3)
        assert result.total == 3
        assert result.unknown == 0
        assert result.solid_approval == 1
        assert result.leaning_disapproval == 1
        assert result.neutral == 1

    def test_more_records_than_entities(self):
        """When status records exceed total entity count (data inconsistency), counts still work."""
        project_id = uuid4()
        records = [
            make_status_record(
                entity_id=uuid4(),
                project_id=project_id,
                status=EntityStatus.SOLID_APPROVAL,
            ),
            make_status_record(
                entity_id=uuid4(),
                project_id=project_id,
                status=EntityStatus.NEUTRAL,
            ),
            make_status_record(
                entity_id=uuid4(),
                project_id=project_id,
                status=EntityStatus.LEANING_DISAPPROVAL,
            ),
        ]
        # Only 2 entities but 3 records — unknown goes negative
        result = self.service.calculate_status_distribution_with_unknowns(records, 2)
        assert result.total == 2
        assert result.solid_approval == 1
        assert result.neutral == 1
        assert result.leaning_disapproval == 1
        assert result.unknown == -1  # Indicates data inconsistency

    def test_multiple_unknown_status_records(self):
        """Multiple UNKNOWN records should each be counted correctly (net zero per record)."""
        project_id = uuid4()
        records = [
            make_status_record(
                entity_id=uuid4(), project_id=project_id, status=EntityStatus.UNKNOWN
            ),
            make_status_record(
                entity_id=uuid4(), project_id=project_id, status=EntityStatus.UNKNOWN
            ),
            make_status_record(
                entity_id=uuid4(),
                project_id=project_id,
                status=EntityStatus.SOLID_APPROVAL,
            ),
        ]
        result = self.service.calculate_status_distribution_with_unknowns(records, 5)
        assert result.total == 5
        # 2 UNKNOWN records (decrement then re-increment = net zero each) + 1 SOLID_APPROVAL
        assert result.unknown == 4  # 5 - 1 (solid_approval) = 4
        assert result.solid_approval == 1


class TestCreateProject:
    """Tests for project creation validation."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.projects_provider = MockDatabaseProvider()
        self.groups_provider = MockDatabaseProvider()
        self.jurisdictions_provider = MockDatabaseProvider()
        self.service = ProjectService(
            projects_provider=self.projects_provider,
            status_records_provider=MockDatabaseProvider(),
            entities_provider=MockDatabaseProvider(),
            jurisdictions_provider=self.jurisdictions_provider,
            groups_provider=self.groups_provider,
        )

    async def test_create_project_validates_group(self):
        """Creating a project with a nonexistent group should raise ValueError."""
        project_base = ProjectBase(
            title="Test",
            group_id=uuid4(),
            jurisdiction_id=None,
        )
        with pytest.raises(ValueError, match="Group not found"):
            await self.service.create_project(project_base)

    async def test_create_project_validates_jurisdiction(self):
        """Creating a project with a nonexistent jurisdiction should raise ValueError."""
        group = make_group()
        self.groups_provider.seed(group)

        project_base = ProjectBase(
            title="Test",
            group_id=group.id,
            jurisdiction_id=uuid4(),
        )
        with pytest.raises(ValueError, match="Jurisdiction not found"):
            await self.service.create_project(project_base)

    async def test_create_project_success(self):
        """Creating a project with valid references should succeed."""
        group = make_group()
        jurisdiction = make_jurisdiction()
        self.groups_provider.seed(group)
        self.jurisdictions_provider.seed(jurisdiction)

        project_base = ProjectBase(
            title="Valid Project",
            group_id=group.id,
            jurisdiction_id=jurisdiction.id,
        )
        result = await self.service.create_project(project_base)
        assert result.title == "Valid Project"


class TestListProjects:
    """Tests for list_projects archive filtering."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.projects_provider = MockDatabaseProvider()
        self.entities_provider = MockDatabaseProvider()
        self.jurisdictions_provider = MockDatabaseProvider()
        self.service = ProjectService(
            projects_provider=self.projects_provider,
            status_records_provider=MockDatabaseProvider(),
            entities_provider=self.entities_provider,
            jurisdictions_provider=self.jurisdictions_provider,
            groups_provider=MockDatabaseProvider(),
        )

    async def test_list_excludes_archived_by_default(self):
        """Without explicit status filter, archived projects should be excluded."""
        active_project = make_project(title="Active", status=ProjectStatus.ACTIVE)
        archived_project = make_project(title="Archived", status=ProjectStatus.ARCHIVED)
        self.projects_provider.seed(active_project)
        self.projects_provider.seed(archived_project)

        results = await self.service.list_projects()
        titles = [p.title for p in results]
        assert "Active" in titles
        assert "Archived" not in titles

    async def test_list_with_archived_status_filter(self):
        """Explicitly filtering by ARCHIVED should return only archived projects."""
        active_project = make_project(title="Active", status=ProjectStatus.ACTIVE)
        archived_project = make_project(title="Archived", status=ProjectStatus.ARCHIVED)
        self.projects_provider.seed(active_project)
        self.projects_provider.seed(archived_project)

        results = await self.service.list_projects(status=ProjectStatus.ARCHIVED)
        titles = [p.title for p in results]
        assert "Active" not in titles
        assert "Archived" in titles


class TestGetProjectBySlug:
    """Tests for slug-based project lookup."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.projects_provider = MockDatabaseProvider()
        self.jurisdictions_provider = MockDatabaseProvider()
        self.service = ProjectService(
            projects_provider=self.projects_provider,
            status_records_provider=MockDatabaseProvider(),
            entities_provider=MockDatabaseProvider(),
            jurisdictions_provider=self.jurisdictions_provider,
            groups_provider=MockDatabaseProvider(),
        )

    async def test_get_project_by_slug_returns_project_when_found(self):
        """Slug-based lookup returns the matching project."""
        project = make_project(slug="my-slug")
        self.projects_provider.seed(project)

        result = await self.service.get_project_by_slug("my-slug")
        assert result is not None
        assert result.id == project.id

    async def test_get_project_by_slug_returns_none_when_not_found(self):
        """Slug-based lookup returns None for absent slug."""
        result = await self.service.get_project_by_slug("nonexistent-slug")
        assert result is None

    async def test_get_project_by_slug_returns_enriched_project(self):
        """Returned project has jurisdiction_name populated."""
        jurisdiction = make_jurisdiction(name="Test City Council")
        self.jurisdictions_provider.seed(jurisdiction)

        project = make_project(slug="enriched-slug", jurisdiction_id=jurisdiction.id)
        self.projects_provider.seed(project)

        result = await self.service.get_project_by_slug("enriched-slug")
        assert result is not None
        assert result.jurisdiction_name == "Test City Council"
