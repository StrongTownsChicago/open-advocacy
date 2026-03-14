"""Tests for EntityService business logic."""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.exceptions import NotFoundError
from app.models.pydantic.models import AddressLookupRequest
from app.services.entity_service import EntityService
from tests.factories import make_district, make_entity, make_jurisdiction
from tests.mock_provider import MockDatabaseProvider


class TestListEntities:
    """Tests for district name enrichment in list_entities."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.entities_provider = MockDatabaseProvider()
        self.jurisdictions_provider = MockDatabaseProvider()
        self.districts_provider = MockDatabaseProvider()
        self.service = EntityService(
            entities_provider=self.entities_provider,
            jurisdictions_provider=self.jurisdictions_provider,
            districts_provider=self.districts_provider,
        )

    async def test_enriches_district_names(self):
        """Entities returned by list_entities should have district_name populated."""
        jurisdiction = make_jurisdiction()
        self.jurisdictions_provider.seed(jurisdiction)

        district = make_district(name="Ward 1", jurisdiction_id=jurisdiction.id)
        self.districts_provider.seed(district)

        entity = make_entity(jurisdiction_id=jurisdiction.id, district_id=district.id)
        self.entities_provider.seed(entity)

        result = await self.service.list_entities(jurisdiction.id)
        assert len(result) == 1
        assert result[0].district_name == "Ward 1"

    async def test_enriches_multiple_entities_district_names(self):
        """3 entities in 3 districts; each entity's district_name matches its district."""
        jurisdiction = make_jurisdiction()
        self.jurisdictions_provider.seed(jurisdiction)

        district_a = make_district(name="Ward 1", jurisdiction_id=jurisdiction.id)
        district_b = make_district(name="Ward 2", jurisdiction_id=jurisdiction.id)
        district_c = make_district(name="Ward 3", jurisdiction_id=jurisdiction.id)
        self.districts_provider.seed(district_a)
        self.districts_provider.seed(district_b)
        self.districts_provider.seed(district_c)

        entity_a = make_entity(
            name="Ald. A", jurisdiction_id=jurisdiction.id, district_id=district_a.id
        )
        entity_b = make_entity(
            name="Ald. B", jurisdiction_id=jurisdiction.id, district_id=district_b.id
        )
        entity_c = make_entity(
            name="Ald. C", jurisdiction_id=jurisdiction.id, district_id=district_c.id
        )
        self.entities_provider.seed(entity_a)
        self.entities_provider.seed(entity_b)
        self.entities_provider.seed(entity_c)

        result = await self.service.list_entities(jurisdiction.id)

        assert len(result) == 3
        names_by_id = {e.id: e.district_name for e in result}
        assert names_by_id[entity_a.id] == "Ward 1"
        assert names_by_id[entity_b.id] == "Ward 2"
        assert names_by_id[entity_c.id] == "Ward 3"

    async def test_handles_missing_district_gracefully(self):
        """Entities with a district_id that has no matching district should not crash."""
        jurisdiction = make_jurisdiction()
        self.jurisdictions_provider.seed(jurisdiction)

        missing_district_id = uuid4()
        entity = make_entity(
            jurisdiction_id=jurisdiction.id, district_id=missing_district_id
        )
        self.entities_provider.seed(entity)

        result = await self.service.list_entities(jurisdiction.id)
        assert len(result) == 1
        assert result[0].district_name is None


class TestCreateEntity:
    """Tests for jurisdiction validation in create_entity."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.entities_provider = MockDatabaseProvider()
        self.jurisdictions_provider = MockDatabaseProvider()
        self.districts_provider = MockDatabaseProvider()
        self.service = EntityService(
            entities_provider=self.entities_provider,
            jurisdictions_provider=self.jurisdictions_provider,
            districts_provider=self.districts_provider,
        )

    async def test_validates_jurisdiction_exists(self):
        """Creating an entity with a nonexistent jurisdiction should raise NotFoundError."""
        from app.models.pydantic.models import EntityCreate

        entity_create = EntityCreate(
            name="Test",
            entity_type="alderman",
            jurisdiction_id=uuid4(),
            district_id=uuid4(),
        )
        with pytest.raises(NotFoundError, match="Jurisdiction not found"):
            await self.service.create_entity(entity_create)

    async def test_succeeds_with_valid_jurisdiction(self):
        """Creating an entity with a valid jurisdiction should succeed."""
        from app.models.pydantic.models import EntityCreate

        jurisdiction = make_jurisdiction()
        self.jurisdictions_provider.seed(jurisdiction)

        entity_create = EntityCreate(
            name="Test Entity",
            entity_type="alderman",
            jurisdiction_id=jurisdiction.id,
            district_id=uuid4(),
        )
        result = await self.service.create_entity(entity_create)
        assert result.name == "Test Entity"


class TestLookupEntitiesByAddress:
    """Tests for the address lookup chain."""

    async def test_raises_without_geo_provider(self):
        """lookup_entities_by_address should raise ValueError when geo_provider is None."""
        service = EntityService(
            entities_provider=MockDatabaseProvider(),
            jurisdictions_provider=MockDatabaseProvider(),
            districts_provider=MockDatabaseProvider(),
            geo_provider=None,
        )
        request = AddressLookupRequest(address="123 Main St")
        with pytest.raises(ValueError, match="Geo provider is required"):
            await service.lookup_entities_by_address(request)

    async def test_full_lookup_chain(self):
        """The full lookup chain should geocode, find districts, find entities, and enrich."""
        entities_provider = MockDatabaseProvider()
        jurisdictions_provider = MockDatabaseProvider()
        districts_provider = MockDatabaseProvider()

        # Set up test data
        jurisdiction = make_jurisdiction()
        jurisdictions_provider.seed(jurisdiction)

        district = make_district(name="Ward 5", jurisdiction_id=jurisdiction.id)
        districts_provider.seed(district)

        entity = make_entity(
            name="Ald. Smith",
            jurisdiction_id=jurisdiction.id,
            district_id=district.id,
        )
        entities_provider.seed(entity)

        # Create mock geo provider
        mock_geo = AsyncMock()
        mock_geo.districts_containing_point = AsyncMock(return_value=[district.id])

        service = EntityService(
            entities_provider=entities_provider,
            jurisdictions_provider=jurisdictions_provider,
            districts_provider=districts_provider,
            geo_provider=mock_geo,
        )

        # Mock the geocoding service
        with patch.object(
            service.geocoding_service,
            "geocode_address",
            new_callable=AsyncMock,
            return_value=(41.8781, -87.6298),
        ):
            request = AddressLookupRequest(address="123 Main St, Chicago, IL")
            result = await service.lookup_entities_by_address(request)

        assert len(result) == 1
        assert result[0].name == "Ald. Smith"
        assert result[0].district_name == "Ward 5"
        mock_geo.districts_containing_point.assert_called_once_with(41.8781, -87.6298)

    async def test_no_districts_found_returns_empty(self):
        """When no districts contain the geocoded point, should return empty list."""
        mock_geo = AsyncMock()
        mock_geo.districts_containing_point = AsyncMock(return_value=[])

        service = EntityService(
            entities_provider=MockDatabaseProvider(),
            jurisdictions_provider=MockDatabaseProvider(),
            districts_provider=MockDatabaseProvider(),
            geo_provider=mock_geo,
        )

        with patch.object(
            service.geocoding_service,
            "geocode_address",
            new_callable=AsyncMock,
            return_value=(41.8781, -87.6298),
        ):
            request = AddressLookupRequest(address="123 Main St, Chicago, IL")
            result = await service.lookup_entities_by_address(request)

        assert result == []

    async def test_districts_found_but_no_entities(self):
        """When districts are found but no entities exist in them, returns empty list."""
        district = make_district(name="Ward 99")
        districts_provider = MockDatabaseProvider()
        districts_provider.seed(district)

        mock_geo = AsyncMock()
        mock_geo.districts_containing_point = AsyncMock(return_value=[district.id])

        service = EntityService(
            entities_provider=MockDatabaseProvider(),  # empty — no entities
            jurisdictions_provider=MockDatabaseProvider(),
            districts_provider=districts_provider,
            geo_provider=mock_geo,
        )

        with patch.object(
            service.geocoding_service,
            "geocode_address",
            new_callable=AsyncMock,
            return_value=(41.8781, -87.6298),
        ):
            request = AddressLookupRequest(address="123 Main St, Chicago, IL")
            result = await service.lookup_entities_by_address(request)

        assert result == []
