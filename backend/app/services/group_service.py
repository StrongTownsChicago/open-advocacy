import re
from uuid import UUID

from app.models.pydantic.models import Group, GroupBase
from app.db.base import DatabaseProvider


def _name_to_slug(name: str) -> str:
    """Convert a group name to a URL slug, e.g. 'Strong Towns Chicago' → 'strong-towns-chicago'."""
    slug = name.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


class GroupService:
    def __init__(
        self,
        groups_provider: DatabaseProvider,
    ):
        self.groups_provider = groups_provider

    async def list_groups(self) -> list[Group]:
        """List all groups."""
        return await self.groups_provider.list()

    async def create_group(self, group: GroupBase) -> Group:
        """Create a new group."""
        return await self.groups_provider.create(group)

    async def get_group(self, group_id: UUID) -> Group | None:
        """Get a group by ID."""
        return await self.groups_provider.get(group_id)

    async def update_group(self, group_id: UUID, group: GroupBase) -> Group | None:
        """Update an existing group."""
        existing_group = await self.groups_provider.get(group_id)
        if not existing_group:
            return None

        return await self.groups_provider.update(group_id, group)

    async def delete_group(self, group_id: UUID) -> bool:
        """Delete a group by ID."""
        existing_group = await self.groups_provider.get(group_id)
        if not existing_group:
            return False

        return await self.groups_provider.delete(group_id)

    async def find_by_slug(self, slug: str) -> Group | None:
        """Find a group by its name-derived slug, e.g. 'strong-towns-chicago'."""
        groups = await self.groups_provider.list()
        for group in groups:
            if _name_to_slug(group.name) == slug:
                return group
        return None

    async def find_or_create_by_name(self, name: str, description: str) -> Group:
        """Find a group by name or create it if it doesn't exist."""
        results = await self.groups_provider.filter(name=name)
        existing_group = results[0] if results else None

        if existing_group:
            return existing_group

        return await self.create_group(GroupBase(name=name, description=description))
