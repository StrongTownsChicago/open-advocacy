"""Tests for JurisdictionService business logic."""

import pytest

from app.services.jurisdiction_service import JurisdictionService
from tests.factories import make_jurisdiction
from tests.mock_provider import MockDatabaseProvider


class TestFindByName:
    """Tests for the find_by_name method — the only method with real logic."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.jurisdictions_provider = MockDatabaseProvider()
        self.service = JurisdictionService(
            jurisdictions_provider=self.jurisdictions_provider
        )

    async def test_find_by_name_found(self):
        """Returns the jurisdiction matching the exact name."""
        jurisdiction = make_jurisdiction(name="Chicago City Council")
        self.jurisdictions_provider.seed(jurisdiction)

        result = await self.service.find_by_name("Chicago City Council")

        assert result is not None
        assert result.id == jurisdiction.id

    async def test_find_by_name_not_found(self):
        """Returns None when no jurisdiction has the given name."""
        result = await self.service.find_by_name("Nonexistent")

        assert result is None

    async def test_find_by_name_returns_correct_match(self):
        """With 3 jurisdictions in the store, returns only the one with the matching name."""
        j1 = make_jurisdiction(name="Chicago City Council")
        j2 = make_jurisdiction(name="Illinois State Senate")
        j3 = make_jurisdiction(name="Cook County Board")
        self.jurisdictions_provider.seed(j1)
        self.jurisdictions_provider.seed(j2)
        self.jurisdictions_provider.seed(j3)

        result = await self.service.find_by_name("Illinois State Senate")

        assert result is not None
        assert result.id == j2.id
        assert result.name == "Illinois State Senate"
