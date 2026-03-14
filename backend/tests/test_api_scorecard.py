"""Tests for GET /api/scorecard/{group_slug} route."""

from typing import cast
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.pydantic.models import Group
from app.services.group_service import GroupService
from app.services.scorecard_service import ScorecardService
from app.services.service_factory import get_group_service, get_scorecard_service
from tests.mock_provider import MockDatabaseProvider


def _build_empty_scorecard_service() -> ScorecardService:
    """Build a ScorecardService that returns an empty scorecard."""
    return ScorecardService(
        projects_provider=MockDatabaseProvider(),
        entities_provider=MockDatabaseProvider(),
        status_records_provider=MockDatabaseProvider(),
        districts_provider=MockDatabaseProvider(),
    )


def _build_group_service_returning(group: Group | None) -> GroupService:
    """Build a GroupService stub whose find_by_slug always returns the given group."""
    mock = MagicMock(spec=GroupService)
    mock.find_by_slug = AsyncMock(return_value=group)
    return cast(GroupService, mock)


class TestScorecardEndpoint:
    @pytest.fixture(autouse=True)
    def setup(self):
        group = Group(id=uuid4(), name="Test Group")
        app.dependency_overrides[get_scorecard_service] = lambda: _build_empty_scorecard_service()
        app.dependency_overrides[get_group_service] = lambda: _build_group_service_returning(group)
        yield
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_endpoint_requires_no_auth(self):
        """GET /api/scorecard/{slug} returns 200 without an Authorization header."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/scorecard/test-group")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_unknown_group_slug_returns_404(self):
        """GET /api/scorecard/{slug} returns 404 when no group matches the slug."""
        app.dependency_overrides[get_group_service] = lambda: _build_group_service_returning(None)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/scorecard/no-such-group")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_response_has_correct_shape(self):
        """Response body has 'projects' and 'entities' keys."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/scorecard/test-group")
        assert response.status_code == 200
        body = response.json()
        assert "projects" in body
        assert "entities" in body
        assert isinstance(body["projects"], list)
        assert isinstance(body["entities"], list)

    @pytest.mark.asyncio
    async def test_response_is_empty_for_group_with_no_projects(self):
        """A group with no active projects should return empty lists (not an error)."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/scorecard/test-group")
        body = response.json()
        assert body["projects"] == []
        assert body["entities"] == []
