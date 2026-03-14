"""API integration tests for the /api/status route."""

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.auth import get_active_user
from app.main import app
from app.models.pydantic.models import EntityStatus
from app.services.service_factory import get_status_service
from app.services.status_service import StatusService
from tests.factories import make_entity, make_project, make_status_record, make_user
from tests.mock_provider import MockDatabaseProvider


def _build_status_service():
    status_records_provider = MockDatabaseProvider()
    projects_provider = MockDatabaseProvider()
    entities_provider = MockDatabaseProvider()
    return StatusService(
        status_records_provider=status_records_provider,
        projects_provider=projects_provider,
        entities_provider=entities_provider,
    )


class TestStatusRoutes:
    """Auth enforcement and error mapping for the status route."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.status_service = _build_status_service()
        app.dependency_overrides[get_status_service] = lambda: self.status_service
        yield
        app.dependency_overrides.clear()

    def _valid_record_payload(self, project_id=None, entity_id=None):
        return {
            "id": str(uuid4()),
            "entity_id": str(entity_id or uuid4()),
            "project_id": str(project_id or uuid4()),
            "status": EntityStatus.NEUTRAL.value,
            "updated_by": "test_user",
            "updated_at": "2024-01-01T00:00:00",
        }

    async def test_create_status_requires_auth(self):
        """POST /api/status/ without token → 401."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/status/", json=self._valid_record_payload()
            )
        assert response.status_code == 401

    async def test_create_status_success(self):
        """POST with valid payload + auth → 200."""
        project = make_project()
        entity = make_entity()
        self.status_service.projects_provider.seed(project)
        self.status_service.entities_provider.seed(entity)

        async def mock_active_user():
            return make_user()

        app.dependency_overrides[get_active_user] = mock_active_user

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/status/",
                json=self._valid_record_payload(
                    project_id=project.id, entity_id=entity.id
                ),
                headers={"Authorization": "Bearer fake"},
            )
        assert response.status_code == 200

    async def test_create_status_project_not_found(self):
        """POST with non-existent project_id → 404."""
        entity = make_entity()
        self.status_service.entities_provider.seed(entity)

        async def mock_active_user():
            return make_user()

        app.dependency_overrides[get_active_user] = mock_active_user

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/status/",
                json=self._valid_record_payload(
                    project_id=uuid4(), entity_id=entity.id
                ),
                headers={"Authorization": "Bearer fake"},
            )
        assert response.status_code == 404
        assert "Project not found" in response.json()["detail"]

    async def test_create_status_entity_not_found(self):
        """POST with non-existent entity_id → 404."""
        project = make_project()
        self.status_service.projects_provider.seed(project)

        async def mock_active_user():
            return make_user()

        app.dependency_overrides[get_active_user] = mock_active_user

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/status/",
                json=self._valid_record_payload(
                    project_id=project.id, entity_id=uuid4()
                ),
                headers={"Authorization": "Bearer fake"},
            )
        assert response.status_code == 404
        assert "Entity not found" in response.json()["detail"]

    async def test_create_status_upserts(self):
        """POST twice with same entity+project pair → second call updates, total records = 1."""
        project = make_project()
        entity = make_entity()
        self.status_service.projects_provider.seed(project)
        self.status_service.entities_provider.seed(entity)

        async def mock_active_user():
            return make_user()

        app.dependency_overrides[get_active_user] = mock_active_user

        payload = self._valid_record_payload(project_id=project.id, entity_id=entity.id)
        updated_payload = {**payload, "status": EntityStatus.SOLID_APPROVAL.value}

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.post(
                "/api/status/",
                json=payload,
                headers={"Authorization": "Bearer fake"},
            )
            response = await client.post(
                "/api/status/",
                json=updated_payload,
                headers={"Authorization": "Bearer fake"},
            )

        assert response.status_code == 200
        all_records = await self.status_service.status_records_provider.list()
        assert len(all_records) == 1

    async def test_get_status_not_found(self):
        """GET /api/status/{random_uuid} → 404."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/status/{uuid4()}")
        assert response.status_code == 404

    async def test_update_status_requires_auth(self):
        """PUT /api/status/{id} without token → 401."""
        record = make_status_record()
        self.status_service.status_records_provider.seed(record)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.put(
                f"/api/status/{record.id}",
                json=self._valid_record_payload(),
            )
        assert response.status_code == 401

    async def test_delete_status_requires_auth(self):
        """DELETE /api/status/{id} without token → 401."""
        record = make_status_record()
        self.status_service.status_records_provider.seed(record)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.delete(f"/api/status/{record.id}")
        assert response.status_code == 401

    async def test_list_status_filters_by_project_id(self):
        """GET ?project_id=X with mixed records → only returns project X records."""
        project_a = make_project()
        project_b = make_project()
        entity = make_entity()
        self.status_service.projects_provider.seed(project_a)
        self.status_service.projects_provider.seed(project_b)
        self.status_service.entities_provider.seed(entity)

        r1 = make_status_record(project_id=project_a.id, entity_id=entity.id)
        r2 = make_status_record(project_id=project_a.id, entity_id=entity.id)
        r3 = make_status_record(project_id=project_b.id, entity_id=entity.id)
        self.status_service.status_records_provider.seed(r1)
        self.status_service.status_records_provider.seed(r2)
        self.status_service.status_records_provider.seed(r3)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/status/?project_id={project_a.id}")
        assert response.status_code == 200
        results = response.json()
        assert len(results) == 2
        assert all(r["project_id"] == str(project_a.id) for r in results)
