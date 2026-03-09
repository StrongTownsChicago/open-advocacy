from uuid import UUID
from typing import Any

from app.imports.base import DataImporter
from app.services.jurisdiction_service import JurisdictionService
from app.models.pydantic.models import JurisdictionBase


class JurisdictionImporter(DataImporter):
    """Importer for jurisdiction data."""

    def __init__(self, jurisdiction_service: JurisdictionService):
        self.jurisdiction_service = jurisdiction_service

    async def import_data(
        self,
        name: str = "",
        description: str = "",
        level: str = "",
        id: UUID | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Import a jurisdiction."""
        jurisdiction = JurisdictionBase(name=name, description=description, level=level)

        # Check if jurisdiction already exists by name
        existing_jurisdictions = await self.jurisdiction_service.list_jurisdictions()
        existing_by_name = next(
            (j for j in existing_jurisdictions if j.name == name), None
        )

        if id:
            # If ID is provided, use it to get/update jurisdiction
            existing = await self.jurisdiction_service.get_jurisdiction(id)
            if existing:
                result = await self.jurisdiction_service.update_jurisdiction(
                    id, jurisdiction
                )
                return {"operation": "updated", "jurisdiction": result}
        elif existing_by_name:
            # If no ID but name exists, update by name
            result = await self.jurisdiction_service.update_jurisdiction(
                existing_by_name.id, jurisdiction
            )
            return {"operation": "updated", "jurisdiction": result}

        # Create new
        result = await self.jurisdiction_service.create_jurisdiction(jurisdiction)
        return {"operation": "created", "jurisdiction": result}

    async def validate_import(self, **kwargs: Any) -> bool:
        """Validate jurisdiction data."""
        required = ["name", "description", "level"]
        return all(field in kwargs for field in required)
