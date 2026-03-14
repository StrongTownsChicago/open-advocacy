"""Tests for GroupService business logic."""

import pytest

from app.services.group_service import GroupService
from tests.factories import make_group
from tests.mock_provider import MockDatabaseProvider


class TestFindOrCreateByName:
    """Tests for find_or_create_by_name — the only method with real logic."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.groups_provider = MockDatabaseProvider()
        self.service = GroupService(groups_provider=self.groups_provider)

    async def test_find_or_create_returns_existing(self):
        """Seeds a group, calls with same name → returns existing, no second record created."""
        group = make_group(name="Chicago Advocates")
        self.groups_provider.seed(group)

        result = await self.service.find_or_create_by_name(
            "Chicago Advocates", "A description"
        )

        assert result.id == group.id
        all_groups = await self.groups_provider.list()
        assert len(all_groups) == 1

    async def test_find_or_create_creates_new(self):
        """Empty store → creates and returns a new group with the given name."""
        result = await self.service.find_or_create_by_name("New Group", "A new group")

        assert result.name == "New Group"

    async def test_find_or_create_name_match_is_exact(self):
        """'Chicago' in store, call with 'chicago' → creates a new group (case-sensitive match)."""
        group = make_group(name="Chicago")
        self.groups_provider.seed(group)

        result = await self.service.find_or_create_by_name("chicago", "lowercase")

        # Case-sensitive: "chicago" != "Chicago", so a new group is created
        assert result.name == "chicago"
