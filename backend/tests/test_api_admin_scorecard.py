"""Tests for POST /api/admin/scorecard/refresh route."""

from typing import cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.auth import get_active_user, get_password_hash, get_super_admin_user
from app.main import app
from app.models.pydantic.models import UserRole
from app.services.entity_service import EntityService
from app.services.jurisdiction_service import JurisdictionService
from app.services.project_service import ProjectService
from app.services.service_factory import (
    get_entity_service,
    get_jurisdiction_service,
    get_project_service,
    get_status_service,
)
from app.services.status_service import StatusService
from tests.factories import make_jurisdiction, make_user

_TEST_RESULT = {"updated": 42, "errors": 0}

_SUPER_ADMIN = make_user(
    email="superadmin@test.com",
    name="Super Admin",
    role=UserRole.SUPER_ADMIN,
    hashed_password=get_password_hash("testpass"),
)

_GROUP_ADMIN = make_user(
    email="groupadmin@test.com",
    name="Group Admin",
    role=UserRole.GROUP_ADMIN,
    hashed_password=get_password_hash("testpass"),
)


def _make_mock_services() -> tuple[
    EntityService, JurisdictionService, ProjectService, StatusService
]:
    jurisdiction = make_jurisdiction(name="Chicago City Council")
    entity_service = MagicMock(spec=EntityService)
    entity_service.list_entities = AsyncMock(return_value=[])
    jurisdiction_service = MagicMock(spec=JurisdictionService)
    jurisdiction_service.find_by_name = AsyncMock(return_value=jurisdiction)
    project_service = MagicMock(spec=ProjectService)
    project_service.get_project_by_slug = AsyncMock(return_value=None)
    status_service = MagicMock(spec=StatusService)
    status_service.create_status_record = AsyncMock(return_value=None)
    return (
        cast(EntityService, entity_service),
        cast(JurisdictionService, jurisdiction_service),
        cast(ProjectService, project_service),
        cast(StatusService, status_service),
    )


class TestScorecardRefreshAuth:
    """Test authentication and authorization for the refresh endpoint."""

    @pytest.fixture(autouse=True)
    def setup(self):
        entity_svc, jurisdiction_svc, project_svc, status_svc = _make_mock_services()
        app.dependency_overrides[get_entity_service] = lambda: entity_svc
        app.dependency_overrides[get_jurisdiction_service] = lambda: jurisdiction_svc
        app.dependency_overrides[get_project_service] = lambda: project_svc
        app.dependency_overrides[get_status_service] = lambda: status_svc
        yield
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_refresh_returns_401_without_token(self):
        """POST /api/admin/scorecard/refresh with no token returns 401."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/admin/scorecard/refresh")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_returns_403_for_group_admin(self):
        """POST with a group_admin user (not super_admin) returns 403."""

        async def _group_admin_override():
            return _GROUP_ADMIN

        app.dependency_overrides[get_active_user] = _group_admin_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/admin/scorecard/refresh",
                headers={"Authorization": "Bearer any-token"},
            )
        assert response.status_code == 403


class TestScorecardRefreshEndpoint:
    """Test the refresh endpoint with a super admin user."""

    @pytest.fixture(autouse=True)
    def setup(self):
        entity_svc, jurisdiction_svc, project_svc, status_svc = _make_mock_services()
        app.dependency_overrides[get_entity_service] = lambda: entity_svc
        app.dependency_overrides[get_jurisdiction_service] = lambda: jurisdiction_svc
        app.dependency_overrides[get_project_service] = lambda: project_svc
        app.dependency_overrides[get_status_service] = lambda: status_svc

        async def _super_admin_override():
            return _SUPER_ADMIN

        app.dependency_overrides[get_super_admin_user] = _super_admin_override
        yield
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_refresh_returns_200_for_super_admin(self):
        """Super admin with mocked service gets 200."""
        with patch(
            "app.api.routes.admin.scorecard.run_scorecard_refresh",
            new=AsyncMock(return_value=_TEST_RESULT),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                response = await client.post("/api/admin/scorecard/refresh")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_refresh_response_body_matches_service_return(self):
        """Response JSON matches what the service returns."""
        with patch(
            "app.api.routes.admin.scorecard.run_scorecard_refresh",
            new=AsyncMock(return_value=_TEST_RESULT),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                response = await client.post("/api/admin/scorecard/refresh")
        assert response.json() == {"updated": 42, "errors": 0}

    @pytest.mark.asyncio
    async def test_refresh_response_has_updated_and_errors_keys(self):
        """Response body has 'updated' and 'errors' keys."""
        with patch(
            "app.api.routes.admin.scorecard.run_scorecard_refresh",
            new=AsyncMock(return_value={"updated": 10, "errors": 2}),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                response = await client.post("/api/admin/scorecard/refresh")
        body = response.json()
        assert "updated" in body
        assert "errors" in body

    @pytest.mark.asyncio
    async def test_refresh_returns_500_on_service_exception(self):
        """When the service raises, the route returns 500 with a descriptive detail."""
        with patch(
            "app.api.routes.admin.scorecard.run_scorecard_refresh",
            new=AsyncMock(side_effect=RuntimeError("eLMS unreachable")),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                response = await client.post("/api/admin/scorecard/refresh")
        assert response.status_code == 500
        assert "Scorecard refresh failed" in response.json()["detail"]
