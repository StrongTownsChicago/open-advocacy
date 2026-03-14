from uuid import UUID

from app.models.pydantic.models import (
    Jurisdiction,
    JurisdictionBase,
)
from app.db.base import DatabaseProvider


class JurisdictionService:
    def __init__(
        self,
        jurisdictions_provider: DatabaseProvider,
    ):
        self.jurisdictions_provider = jurisdictions_provider

    async def get_jurisdiction(self, jurisdiction_id: UUID) -> Jurisdiction | None:
        """Get a jurisdiction by ID."""
        return await self.jurisdictions_provider.get(jurisdiction_id)

    async def list_jurisdictions(
        self, skip: int = 0, limit: int = 100
    ) -> list[Jurisdiction]:
        """List all jurisdictions."""
        return await self.jurisdictions_provider.list(skip=skip, limit=limit)

    async def create_jurisdiction(self, jurisdiction: JurisdictionBase) -> Jurisdiction:
        """Create a new jurisdiction."""
        return await self.jurisdictions_provider.create(jurisdiction)

    async def update_jurisdiction(
        self, jurisdiction_id: UUID, jurisdiction: JurisdictionBase
    ) -> Jurisdiction | None:
        """Update an existing jurisdiction."""
        return await self.jurisdictions_provider.update(jurisdiction_id, jurisdiction)

    async def delete_jurisdiction(self, jurisdiction_id: UUID) -> bool:
        """Delete a jurisdiction by ID."""
        return await self.jurisdictions_provider.delete(jurisdiction_id)

    async def find_by_name(self, name: str) -> Jurisdiction | None:
        """Find a jurisdiction by name."""
        results = await self.jurisdictions_provider.filter(name=name)
        return results[0] if results else None
