"""Tests for StatusService validation logic."""

from uuid import uuid4

import pytest

from app.models.pydantic.models import EntityStatus
from tests.factories import make_entity, make_project, make_status_record
from tests.mock_provider import MockDatabaseProvider


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
        """Creating a status record with nonexistent project should raise ValueError."""
        entity = make_entity()
        self.entities_provider.seed(entity)

        record = make_status_record(
            entity_id=entity.id,
            project_id=uuid4(),
            status=EntityStatus.NEUTRAL,
        )
        with pytest.raises(ValueError, match="Project not found"):
            await self.service.create_status_record(record)

    async def test_create_raises_for_missing_entity(self):
        """Creating a status record with nonexistent entity should raise ValueError."""
        project = make_project()
        self.projects_provider.seed(project)

        record = make_status_record(
            entity_id=uuid4(),
            project_id=project.id,
            status=EntityStatus.NEUTRAL,
        )
        with pytest.raises(ValueError, match="Entity not found"):
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
