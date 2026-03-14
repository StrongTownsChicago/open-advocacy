"""API integration tests for the /api/groups route."""

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.auth import get_active_user
from app.main import app
from app.services.group_service import GroupService
from app.services.service_factory import get_group_service
from tests.factories import make_group, make_user
from tests.mock_provider import MockDatabaseProvider


def _build_group_service():
    return GroupService(groups_provider=MockDatabaseProvider())


class TestGroupRoutes:
    """Auth enforcement and error mapping for the groups route."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.group_service = _build_group_service()
        app.dependency_overrides[get_group_service] = lambda: self.group_service
        yield
        app.dependency_overrides.clear()

    async def test_create_group_requires_auth(self):
        """POST /api/groups/ without token → 401."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/groups/",
                json={"name": "Test Group", "description": "A test group"},
            )
        assert response.status_code == 401

    async def test_create_group_success(self):
        """POST with valid payload + auth → 200."""

        async def mock_active_user():
            return make_user()

        app.dependency_overrides[get_active_user] = mock_active_user

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/groups/",
                json={"name": "Chicago Advocates", "description": "Civic org"},
                headers={"Authorization": "Bearer fake"},
            )
        assert response.status_code == 200
        assert response.json()["name"] == "Chicago Advocates"

    async def test_get_group_not_found(self):
        """GET /api/groups/{random_uuid} → 404."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/groups/{uuid4()}")
        assert response.status_code == 404

    async def test_update_group_requires_auth(self):
        """PUT /api/groups/{id} without token → 401."""
        group = make_group()
        self.group_service.groups_provider.seed(group)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.put(
                f"/api/groups/{group.id}",
                json={"name": "Updated", "description": "Updated"},
            )
        assert response.status_code == 401

    async def test_delete_group_requires_auth(self):
        """DELETE /api/groups/{id} without token → 401."""
        group = make_group()
        self.group_service.groups_provider.seed(group)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.delete(f"/api/groups/{group.id}")
        assert response.status_code == 401
