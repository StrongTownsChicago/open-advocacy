"""Tests for projects API route auth enforcement and error mapping."""

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.service_factory import get_project_service
from app.services.project_service import ProjectService
from tests.mock_provider import MockDatabaseProvider


def _build_project_service() -> ProjectService:
    """Create a ProjectService backed by mock providers."""
    return ProjectService(
        projects_provider=MockDatabaseProvider(),
        status_records_provider=MockDatabaseProvider(),
        entities_provider=MockDatabaseProvider(),
        jurisdictions_provider=MockDatabaseProvider(),
        groups_provider=MockDatabaseProvider(),
    )


class TestProjectsAuthEnforcement:
    """Test that auth is properly wired on project endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.service = _build_project_service()
        app.dependency_overrides[get_project_service] = lambda: self.service
        yield
        app.dependency_overrides.clear()

    async def test_list_projects_no_auth_required(self):
        """GET /api/projects should succeed without authentication."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/projects/")
        assert response.status_code == 200

    async def test_create_project_requires_auth(self):
        """POST /api/projects without a token should return 401."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/projects/",
                json={
                    "title": "Unauthorized Project",
                    "jurisdiction_id": str(uuid4()),
                    "group_id": str(uuid4()),
                },
            )
        assert response.status_code == 401

    async def test_get_nonexistent_project_returns_404(self):
        """GET /api/projects/{bad_id} should return 404."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/projects/{uuid4()}")
        assert response.status_code == 404

    async def test_delete_requires_auth(self):
        """DELETE /api/projects/{id} without a token should return 401."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete(f"/api/projects/{uuid4()}")
        assert response.status_code == 401
