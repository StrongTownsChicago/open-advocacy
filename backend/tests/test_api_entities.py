"""API integration tests for the /api/entities route."""

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.auth import get_active_user
from app.main import app
from app.services.entity_service import EntityService
from app.services.service_factory import get_entity_service
from tests.factories import make_entity, make_jurisdiction, make_user
from tests.mock_provider import MockDatabaseProvider


def _build_entity_service():
    entities_provider = MockDatabaseProvider()
    jurisdictions_provider = MockDatabaseProvider()
    districts_provider = MockDatabaseProvider()
    service = EntityService(
        entities_provider=entities_provider,
        jurisdictions_provider=jurisdictions_provider,
        districts_provider=districts_provider,
        geo_provider=None,
    )
    return service


class TestEntityRoutes:
    """Auth enforcement and error mapping for the entities route."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.entity_service = _build_entity_service()
        app.dependency_overrides[get_entity_service] = lambda: self.entity_service
        yield
        app.dependency_overrides.clear()

    async def test_create_entity_requires_auth(self):
        """POST /api/entities/ without token → 401."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/entities/",
                json={
                    "name": "Test",
                    "entity_type": "alderman",
                    "jurisdiction_id": str(uuid4()),
                    "district_id": str(uuid4()),
                },
            )
        assert response.status_code == 401

    async def test_create_entity_success(self):
        """POST with valid payload + auth → 200, returned entity matches input."""
        jurisdiction = make_jurisdiction()
        self.entity_service.jurisdictions_provider.seed(jurisdiction)

        async def mock_active_user():
            return make_user()

        app.dependency_overrides[get_active_user] = mock_active_user

        district_id = uuid4()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/entities/",
                json={
                    "name": "Test Alderman",
                    "entity_type": "alderman",
                    "jurisdiction_id": str(jurisdiction.id),
                    "district_id": str(district_id),
                },
                headers={"Authorization": "Bearer fake"},
            )
        assert response.status_code == 200
        body = response.json()
        assert body["name"] == "Test Alderman"

    async def test_create_entity_jurisdiction_not_found(self):
        """POST with non-existent jurisdiction_id → 404."""

        async def mock_active_user():
            return make_user()

        app.dependency_overrides[get_active_user] = mock_active_user

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/entities/",
                json={
                    "name": "Test",
                    "entity_type": "alderman",
                    "jurisdiction_id": str(uuid4()),
                    "district_id": str(uuid4()),
                },
                headers={"Authorization": "Bearer fake"},
            )
        assert response.status_code == 404

    async def test_get_entity_not_found(self):
        """GET /api/entities/{random_uuid} → 404."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/entities/{uuid4()}")
        assert response.status_code == 404

    async def test_update_entity_requires_auth(self):
        """PUT /api/entities/{id} without token → 401."""
        entity = make_entity()
        self.entity_service.entities_provider.seed(entity)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.put(
                f"/api/entities/{entity.id}",
                json={
                    "name": "Updated",
                    "entity_type": "alderman",
                    "jurisdiction_id": str(uuid4()),
                    "district_id": str(uuid4()),
                },
            )
        assert response.status_code == 401

    async def test_delete_entity_requires_auth(self):
        """DELETE /api/entities/{id} without token → 401."""
        entity = make_entity()
        self.entity_service.entities_provider.seed(entity)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.delete(f"/api/entities/{entity.id}")
        assert response.status_code == 401

    async def test_list_entities_by_jurisdiction(self):
        """GET with jurisdiction_id → 200, returns only matching entities."""
        jurisdiction = make_jurisdiction()
        self.entity_service.jurisdictions_provider.seed(jurisdiction)

        entity_in = make_entity(jurisdiction_id=jurisdiction.id)
        entity_out = make_entity(jurisdiction_id=uuid4())
        self.entity_service.entities_provider.seed(entity_in)
        self.entity_service.entities_provider.seed(entity_out)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                f"/api/entities/?jurisdiction_id={jurisdiction.id}"
            )
        assert response.status_code == 200
        ids = [e["id"] for e in response.json()]
        assert str(entity_in.id) in ids
        assert str(entity_out.id) not in ids
