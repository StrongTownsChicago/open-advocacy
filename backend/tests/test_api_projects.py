"""Tests for projects API route auth enforcement and error mapping."""

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.service_factory import get_project_service
from app.services.project_service import ProjectService
from tests.mock_provider import MockDatabaseProvider
from tests.factories import make_project


def _build_project_service() -> tuple[ProjectService, MockDatabaseProvider]:
    """Create a ProjectService backed by mock providers. Returns (service, projects_provider)."""
    projects_provider = MockDatabaseProvider()
    service = ProjectService(
        projects_provider=projects_provider,
        status_records_provider=MockDatabaseProvider(),
        entities_provider=MockDatabaseProvider(),
        jurisdictions_provider=MockDatabaseProvider(),
        groups_provider=MockDatabaseProvider(),
    )
    return service, projects_provider


class TestProjectsAuthEnforcement:
    """Test that auth is properly wired on project endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.service, _ = _build_project_service()
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


class TestProjectSlugEndpoint:
    """Tests for the slug-based project lookup endpoint."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.service, self.projects_provider = _build_project_service()
        app.dependency_overrides[get_project_service] = lambda: self.service
        yield
        app.dependency_overrides.clear()

    async def test_get_project_by_slug_returns_404_when_not_found(self):
        """GET /api/projects/slug/nonexistent should return 404."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/projects/slug/nonexistent-slug")
        assert response.status_code == 404
        assert response.json()["detail"] == "Project not found"

    async def test_get_project_by_slug_returns_project(self):
        """GET /api/projects/slug/{slug} returns the matching project."""
        project = make_project(slug="test-slug", title="Slug Project")
        self.projects_provider.seed(project)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/projects/slug/test-slug")
        assert response.status_code == 200
        assert response.json()["slug"] == "test-slug"
        assert response.json()["title"] == "Slug Project"

    async def test_slug_route_not_confused_with_uuid_route(self):
        """The /slug/ prefix ensures 'not-a-uuid' is not parsed as a UUID."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/projects/slug/not-a-uuid")
        # Should return 404 (slug not found), NOT 422 (UUID validation error)
        assert response.status_code == 404
