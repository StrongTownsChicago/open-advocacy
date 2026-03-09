from uuid import UUID

from app.models.pydantic.models import District, DistrictBase
from app.db.base import DatabaseProvider


class DistrictService:
    def __init__(
        self,
        districts_provider: DatabaseProvider,
        jurisdictions_provider: DatabaseProvider,
    ):
        self.districts_provider = districts_provider
        self.jurisdictions_provider = jurisdictions_provider

    async def get_district(self, district_id: UUID) -> District | None:
        """Get a district by ID."""
        return await self.districts_provider.get(district_id)

    async def list_districts(
        self, jurisdiction_id: UUID | None = None, skip: int = 0, limit: int = 100
    ) -> list[District]:
        """List districts, optionally filtered by jurisdiction."""
        if jurisdiction_id:
            return await self.districts_provider.filter(jurisdiction_id=jurisdiction_id)
        return await self.districts_provider.list(skip=skip, limit=limit)

    async def create_district(self, district: DistrictBase) -> District:
        """Create a new district."""
        # Verify jurisdiction exists
        if district.jurisdiction_id:
            jurisdiction = await self.jurisdictions_provider.get(
                district.jurisdiction_id
            )
            if not jurisdiction:
                raise ValueError("Jurisdiction not found")

        return await self.districts_provider.create(district)

    async def update_district(
        self, district_id: UUID, district: DistrictBase
    ) -> District | None:
        """Update an existing district."""
        # Verify jurisdiction exists if provided
        if district.jurisdiction_id:
            jurisdiction = await self.jurisdictions_provider.get(
                district.jurisdiction_id
            )
            if not jurisdiction:
                raise ValueError("Jurisdiction not found")

        return await self.districts_provider.update(district_id, district)

    async def delete_district(self, district_id: UUID) -> bool:
        """Delete a district by ID."""
        return await self.districts_provider.delete(district_id)

    async def find_district_by_code(
        self, code: str, jurisdiction_id: UUID
    ) -> District | None:
        """Find a district by its code in a specific jurisdiction."""
        districts = await self.districts_provider.filter(
            code=code, jurisdiction_id=jurisdiction_id
        )
        return districts[0] if districts else None
