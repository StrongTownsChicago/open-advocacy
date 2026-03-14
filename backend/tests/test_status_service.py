"""Tests for StatusService validation logic."""

from uuid import uuid4

import pytest

from app.exceptions import NotFoundError
from app.models.pydantic.models import EntityStatus
from tests.factories import make_entity, make_project, make_status_record
from tests.mock_provider import MockDatabaseProvider


class TestListStatusRecords:
    """Tests for filtering logic in list_status_records."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from app.services.status_service import StatusService

        self.status_records_provider = MockDatabaseProvider()
        self.projects_provider = MockDatabaseProvider()
        self.entities_provider = MockDatabaseProvider()
        self.service = StatusService(
            status_records_provider=self.status_records_provider,
            projects_provider=self.projects_provider,
            entities_provider=self.entities_provider,
        )

    async def test_list_no_filter_returns_all(self):
        """No filter returns all records."""
        r1 = make_status_record()
        r2 = make_status_record()
        r3 = make_status_record()
        self.status_records_provider.seed(r1)
        self.status_records_provider.seed(r2)
        self.status_records_provider.seed(r3)

        result = await self.service.list_status_records()

        assert len(result) == 3

    async def test_list_filters_by_project_id(self):
        """3 records (2 for project A, 1 for project B); filtering by project A returns exactly 2."""
        project_a_id = uuid4()
        project_b_id = uuid4()
        r1 = make_status_record(project_id=project_a_id)
        r2 = make_status_record(project_id=project_a_id)
        r3 = make_status_record(project_id=project_b_id)
        self.status_records_provider.seed(r1)
        self.status_records_provider.seed(r2)
        self.status_records_provider.seed(r3)

        result = await self.service.list_status_records(project_id=project_a_id)

        assert len(result) == 2
        assert all(r.project_id == project_a_id for r in result)

    async def test_list_filters_by_entity_id(self):
        """3 records; filtering by entity ID returns only that entity's records."""
        entity_id = uuid4()
        r1 = make_status_record(entity_id=entity_id)
        r2 = make_status_record(entity_id=uuid4())
        r3 = make_status_record(entity_id=uuid4())
        self.status_records_provider.seed(r1)
        self.status_records_provider.seed(r2)
        self.status_records_provider.seed(r3)

        result = await self.service.list_status_records(entity_id=entity_id)

        assert len(result) == 1
        assert result[0].entity_id == entity_id

    async def test_list_filters_by_both(self):
        """Combined project+entity filter returns the single exact match."""
        project_id = uuid4()
        entity_id = uuid4()
        match = make_status_record(project_id=project_id, entity_id=entity_id)
        other_project = make_status_record(project_id=uuid4(), entity_id=entity_id)
        other_entity = make_status_record(project_id=project_id, entity_id=uuid4())
        self.status_records_provider.seed(match)
        self.status_records_provider.seed(other_project)
        self.status_records_provider.seed(other_entity)

        result = await self.service.list_status_records(
            project_id=project_id, entity_id=entity_id
        )

        assert len(result) == 1
        assert result[0].id == match.id


class TestCreateStatusRecordValidation:
    """Tests for validation in create_status_record."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from app.services.status_service import StatusService

        self.status_records_provider = MockDatabaseProvider()
        self.projects_provider = MockDatabaseProvider()
        self.entities_provider = MockDatabaseProvider()
        self.service = StatusService(
            status_records_provider=self.status_records_provider,
            projects_provider=self.projects_provider,
            entities_provider=self.entities_provider,
        )

    async def test_create_raises_for_missing_project(self):
        """Creating a status record with nonexistent project should raise NotFoundError."""
        entity = make_entity()
        self.entities_provider.seed(entity)

        record = make_status_record(
            entity_id=entity.id,
            project_id=uuid4(),
            status=EntityStatus.NEUTRAL,
        )
        with pytest.raises(NotFoundError, match="Project not found"):
            await self.service.create_status_record(record)

    async def test_create_raises_for_missing_entity(self):
        """Creating a status record with nonexistent entity should raise NotFoundError."""
        project = make_project()
        self.projects_provider.seed(project)

        record = make_status_record(
            entity_id=uuid4(),
            project_id=project.id,
            status=EntityStatus.NEUTRAL,
        )
        with pytest.raises(NotFoundError, match="Entity not found"):
            await self.service.create_status_record(record)


class TestCreateStatusRecordUpsert:
    """Tests for the upsert behavior in create_status_record."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from app.services.status_service import StatusService

        self.status_records_provider = MockDatabaseProvider()
        self.projects_provider = MockDatabaseProvider()
        self.entities_provider = MockDatabaseProvider()
        self.service = StatusService(
            status_records_provider=self.status_records_provider,
            projects_provider=self.projects_provider,
            entities_provider=self.entities_provider,
        )

    async def test_creates_new_when_no_existing(self):
        """When no existing record for entity+project, a new record should be created."""
        project = make_project()
        self.projects_provider.seed(project)
        entity = make_entity()
        self.entities_provider.seed(entity)

        record = make_status_record(
            entity_id=entity.id,
            project_id=project.id,
            status=EntityStatus.NEUTRAL,
        )
        result = await self.service.create_status_record(record)

        assert result.entity_id == entity.id
        assert result.project_id == project.id
        assert result.status == EntityStatus.NEUTRAL

        # Verify it was stored
        all_records = await self.status_records_provider.list()
        assert len(all_records) == 1

    async def test_updates_existing_when_entity_project_match(self):
        """When a record for the same entity+project exists, it should be updated."""
        project = make_project()
        self.projects_provider.seed(project)
        entity = make_entity()
        self.entities_provider.seed(entity)

        # Create the initial record
        original_record = make_status_record(
            entity_id=entity.id,
            project_id=project.id,
            status=EntityStatus.UNKNOWN,
        )
        await self.service.create_status_record(original_record)

        # Create a new record with the same entity+project but different status
        updated_record = make_status_record(
            entity_id=entity.id,
            project_id=project.id,
            status=EntityStatus.SOLID_APPROVAL,
        )
        result = await self.service.create_status_record(updated_record)

        assert result.status == EntityStatus.SOLID_APPROVAL

        # Verify no duplicate was created - still only one record
        all_records = await self.status_records_provider.list()
        assert len(all_records) == 1

    async def test_updates_only_matching_record(self):
        """With multiple records, only the one matching entity+project should be updated."""
        project = make_project()
        self.projects_provider.seed(project)
        entity_a = make_entity(name="Entity A")
        entity_b = make_entity(name="Entity B")
        self.entities_provider.seed(entity_a)
        self.entities_provider.seed(entity_b)

        # Create records for both entities
        record_a = make_status_record(
            entity_id=entity_a.id,
            project_id=project.id,
            status=EntityStatus.NEUTRAL,
        )
        record_b = make_status_record(
            entity_id=entity_b.id,
            project_id=project.id,
            status=EntityStatus.NEUTRAL,
        )
        await self.service.create_status_record(record_a)
        await self.service.create_status_record(record_b)

        # Update only entity_a's record
        updated = make_status_record(
            entity_id=entity_a.id,
            project_id=project.id,
            status=EntityStatus.SOLID_APPROVAL,
        )
        result = await self.service.create_status_record(updated)

        assert result.status == EntityStatus.SOLID_APPROVAL

        # Should still have exactly 2 records
        all_records = await self.status_records_provider.list()
        assert len(all_records) == 2

    async def test_create_preserves_metadata(self):
        """Metadata dict should be stored and retrievable after create."""
        project = make_project()
        self.projects_provider.seed(project)
        entity = make_entity()
        self.entities_provider.seed(entity)

        record = make_status_record(
            entity_id=entity.id,
            project_id=project.id,
            status=EntityStatus.SOLID_APPROVAL,
            record_metadata={"rs_zoned_pct": 45.2},
        )
        result = await self.service.create_status_record(record)

        assert result.record_metadata is not None
        assert result.record_metadata["rs_zoned_pct"] == 45.2

    async def test_create_with_none_metadata(self):
        """Creating a record without record_metadata should result in None."""
        project = make_project()
        self.projects_provider.seed(project)
        entity = make_entity()
        self.entities_provider.seed(entity)

        record = make_status_record(
            entity_id=entity.id,
            project_id=project.id,
            status=EntityStatus.NEUTRAL,
        )
        result = await self.service.create_status_record(record)

        assert result.record_metadata is None
