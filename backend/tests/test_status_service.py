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
