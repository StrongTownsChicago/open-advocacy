"""API integration tests for the /api/jurisdictions route."""

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.auth import get_active_user
from app.main import app
from app.services.district_service import DistrictService
from app.services.jurisdiction_service import JurisdictionService
from app.services.service_factory import get_district_service, get_jurisdiction_service
from tests.factories import make_jurisdiction, make_user
from tests.mock_provider import MockDatabaseProvider


def _build_jurisdiction_service():
    return JurisdictionService(
        jurisdictions_provider=MockDatabaseProvider(),
    )


def _build_district_service():
    return DistrictService(
        districts_provider=MockDatabaseProvider(),
        jurisdictions_provider=MockDatabaseProvider(),
    )


class TestJurisdictionRoutes:
    """Auth enforcement, error mapping, and geojson endpoint for jurisdictions route."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.jurisdiction_service = _build_jurisdiction_service()
        self.district_service = _build_district_service()
        app.dependency_overrides[get_jurisdiction_service] = lambda: (
            self.jurisdiction_service
        )
        app.dependency_overrides[get_district_service] = lambda: self.district_service
        yield
        app.dependency_overrides.clear()

    async def test_create_jurisdiction_requires_auth(self):
        """POST /api/jurisdictions/ without token → 401."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/jurisdictions/",
                json={"name": "Test", "description": "Test", "level": "city"},
            )
        assert response.status_code == 401

    async def test_create_jurisdiction_success(self):
        """POST with valid payload + auth → 200."""

        async def mock_active_user():
            return make_user()

        app.dependency_overrides[get_active_user] = mock_active_user

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/jurisdictions/",
                json={
                    "name": "Chicago City Council",
                    "description": "Test",
                    "level": "city",
                },
                headers={"Authorization": "Bearer fake"},
            )
        assert response.status_code == 200
        assert response.json()["name"] == "Chicago City Council"

    async def test_get_jurisdiction_not_found(self):
        """GET /api/jurisdictions/{random_uuid} → 404."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/jurisdictions/{uuid4()}")
        assert response.status_code == 404

    async def test_update_jurisdiction_requires_auth(self):
        """PUT /api/jurisdictions/{id} without token → 401."""
        jurisdiction = make_jurisdiction()
        self.jurisdiction_service.jurisdictions_provider.seed(jurisdiction)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.put(
                f"/api/jurisdictions/{jurisdiction.id}",
                json={"name": "Updated", "description": "Updated", "level": "city"},
            )
        assert response.status_code == 401

    async def test_delete_jurisdiction_requires_auth(self):
        """DELETE /api/jurisdictions/{id} without token → 401."""
        jurisdiction = make_jurisdiction()
        self.jurisdiction_service.jurisdictions_provider.seed(jurisdiction)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.delete(f"/api/jurisdictions/{jurisdiction.id}")
        assert response.status_code == 401

    async def test_get_geojson_with_districts(self):
        """Jurisdiction + 2 districts with boundaries → geojson returns 2 named entries."""
        jurisdiction = make_jurisdiction()
        self.jurisdiction_service.jurisdictions_provider.seed(jurisdiction)

        boundary_a = {
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]],
        }
        boundary_b = {
            "type": "Polygon",
            "coordinates": [[[1, 1], [2, 1], [2, 2], [1, 1]]],
        }

        from app.models.pydantic.models import District

        district_a = District(
            id=uuid4(),
            name="Ward 1",
            jurisdiction_id=jurisdiction.id,
            boundary=boundary_a,
        )
        district_b = District(
            id=uuid4(),
            name="Ward 2",
            jurisdiction_id=jurisdiction.id,
            boundary=boundary_b,
        )
        self.district_service.districts_provider.seed(district_a)
        self.district_service.districts_provider.seed(district_b)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/jurisdictions/{jurisdiction.id}/geojson")
        assert response.status_code == 200
        body = response.json()
        assert "Ward 1" in body
        assert "Ward 2" in body

    async def test_get_geojson_no_districts(self):
        """No districts → 200 with empty dict."""
        jurisdiction = make_jurisdiction()
        self.jurisdiction_service.jurisdictions_provider.seed(jurisdiction)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/jurisdictions/{jurisdiction.id}/geojson")
        assert response.status_code == 200
        assert response.json() == {}
