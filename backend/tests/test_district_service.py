"""Tests for DistrictService business logic."""

from uuid import uuid4

import pytest

from app.exceptions import NotFoundError
from app.models.pydantic.models import DistrictBase
from app.services.district_service import DistrictService
from tests.factories import make_district, make_jurisdiction
from tests.mock_provider import MockDatabaseProvider


class TestCreateDistrict:
    """Tests for jurisdiction validation in create_district."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.districts_provider = MockDatabaseProvider()
        self.jurisdictions_provider = MockDatabaseProvider()
        self.service = DistrictService(
            districts_provider=self.districts_provider,
            jurisdictions_provider=self.jurisdictions_provider,
        )

    async def test_validates_jurisdiction_exists(self):
        """Creating a district with a nonexistent jurisdiction should raise NotFoundError."""
        district = DistrictBase(
            name="Ward 1",
            code="W-01",
            jurisdiction_id=uuid4(),
        )
        with pytest.raises(NotFoundError, match="Jurisdiction not found"):
            await self.service.create_district(district)

    async def test_succeeds_with_valid_jurisdiction(self):
        """Creating a district with a valid jurisdiction should succeed."""
        jurisdiction = make_jurisdiction()
        self.jurisdictions_provider.seed(jurisdiction)

        district = DistrictBase(
            name="Ward 1",
            code="W-01",
            jurisdiction_id=jurisdiction.id,
        )
        result = await self.service.create_district(district)
        assert result.name == "Ward 1"


class TestFindDistrictByCode:
    """Tests for find_district_by_code query logic."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.districts_provider = MockDatabaseProvider()
        self.jurisdictions_provider = MockDatabaseProvider()
        self.service = DistrictService(
            districts_provider=self.districts_provider,
            jurisdictions_provider=self.jurisdictions_provider,
        )

    async def test_found(self):
        """Should return the district when code and jurisdiction match."""
        jurisdiction = make_jurisdiction()
        self.jurisdictions_provider.seed(jurisdiction)

        district = make_district(
            name="Ward 1",
            code="W-01",
            jurisdiction_id=jurisdiction.id,
        )
        self.districts_provider.seed(district)

        result = await self.service.find_district_by_code("W-01", jurisdiction.id)
        assert result is not None
        assert result.name == "Ward 1"
        assert result.code == "W-01"

    async def test_not_found(self):
        """Should return None when no district matches."""
        result = await self.service.find_district_by_code("W-99", uuid4())
        assert result is None


class TestListDistricts:
    """Tests for jurisdiction filtering in list_districts."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.districts_provider = MockDatabaseProvider()
        self.jurisdictions_provider = MockDatabaseProvider()
        self.service = DistrictService(
            districts_provider=self.districts_provider,
            jurisdictions_provider=self.jurisdictions_provider,
        )

    async def test_filters_by_jurisdiction(self):
        """Only districts for the requested jurisdiction should be returned."""
        jur_a = make_jurisdiction(name="City A")
        jur_b = make_jurisdiction(name="City B")
        self.jurisdictions_provider.seed(jur_a)
        self.jurisdictions_provider.seed(jur_b)

        district_a = make_district(name="Ward A-1", jurisdiction_id=jur_a.id)
        district_b = make_district(name="Ward B-1", jurisdiction_id=jur_b.id)
        self.districts_provider.seed(district_a)
        self.districts_provider.seed(district_b)

        result = await self.service.list_districts(jurisdiction_id=jur_a.id)
        assert len(result) == 1
        assert result[0].name == "Ward A-1"

    async def test_lists_all_without_jurisdiction_filter(self):
        """Without a jurisdiction filter, all districts should be returned."""
        jur_a = make_jurisdiction(name="City A")
        jur_b = make_jurisdiction(name="City B")

        district_a = make_district(name="Ward A-1", jurisdiction_id=jur_a.id)
        district_b = make_district(name="Ward B-1", jurisdiction_id=jur_b.id)
        self.districts_provider.seed(district_a)
        self.districts_provider.seed(district_b)

        result = await self.service.list_districts()
        assert len(result) == 2
