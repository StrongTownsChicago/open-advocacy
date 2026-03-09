from uuid import UUID
from typing import Any
import logging

from app.imports.base import DataImporter
from app.services.entity_service import EntityService
from app.services.district_service import DistrictService
from app.services.jurisdiction_service import JurisdictionService
from app.models.pydantic.models import EntityCreate

logger = logging.getLogger(__name__)


class EntityImporter(DataImporter):
    """Importer for entity data."""

    def __init__(
        self,
        entity_service: EntityService,
        district_service: DistrictService,
        jurisdiction_service: JurisdictionService,
    ):
        self.entity_service = entity_service
        self.district_service = district_service
        self.jurisdiction_service = jurisdiction_service

    async def _get_jurisdiction_id(self, jurisdiction_name: str) -> UUID:
        """Get jurisdiction ID from name."""
        jurisdictions = await self.jurisdiction_service.list_jurisdictions()
        jurisdiction = next(
            (j for j in jurisdictions if j.name == jurisdiction_name), None
        )
        if not jurisdiction:
            raise ValueError(f"Jurisdiction not found with name: {jurisdiction_name}")
        return jurisdiction.id

    async def import_data(
        self,
        data: list[dict[str, Any]] | dict[str, list[dict[str, Any]]] | None = None,
        jurisdiction_name: str = "",
        entity_type: str = "",
        title: str = "",
        mapping: dict[str, str | list[str]] | None = None,
        data_key: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Import entities from data source.

        Args:
            data: List of entity data or dict with nested lists
            jurisdiction_name: Name of the parent jurisdiction
            entity_type: Type of entity (e.g., "alderman", "state_representative")
            title: Official title of the entity (e.g., "Alderperson", "State Senator")
            mapping: Dict mapping entity fields to data source fields
            data_key: Optional key to extract data from dict (e.g., "house" or "senate")

        Returns:
            Dict with import results
        """
        if data is None:
            raise ValueError("data is required")
        if mapping is None:
            raise ValueError("mapping is required")

        # Lookup jurisdiction ID from name
        jurisdiction_id = await self._get_jurisdiction_id(jurisdiction_name)

        # Handle data that might be nested under a key
        actual_data: list[dict[str, Any]] = []
        if data_key:
            if not isinstance(data, dict) or data_key not in data:
                raise ValueError(
                    f"Invalid data format: expected dict with key '{data_key}'"
                )
            actual_data = data[data_key]
        elif isinstance(data, list):
            actual_data = data

        # Track results
        created_count = 0
        updated_count = 0
        error_count = 0
        entities = []

        # Process each entity
        for item in actual_data:
            try:
                # Extract entity data using mapping
                entity_data = {}

                # Extract required fields
                name = self._extract_value(item, mapping.get("name", "name"))
                if not name:
                    logger.warning("Skipping entity without name")
                    error_count += 1
                    continue

                entity_data["name"] = name
                entity_data["entity_type"] = entity_type
                entity_data["title"] = title
                entity_data["jurisdiction_id"] = jurisdiction_id

                # Find district if district code is provided
                district_code = self._extract_value(
                    item, mapping.get("district_code", None)
                )
                if district_code:
                    district = await self.district_service.find_district_by_code(
                        code=str(district_code), jurisdiction_id=jurisdiction_id
                    )

                    if district:
                        entity_data["district_id"] = district.id
                    else:
                        logger.warning(f"District with code {district_code} not found")

                # Extract optional fields if provided in mapping
                for field in ["email", "phone", "website", "address", "image_url"]:
                    if field in mapping:
                        value = self._extract_value(item, mapping[field])
                        if value:
                            entity_data[field] = value

                # Check if entity already exists (by name and jurisdiction)
                existing_entities = await self.entity_service.list_entities(
                    jurisdiction_id
                )
                existing_entity = next(
                    (e for e in existing_entities if e.name == name), None
                )

                # Create or update entity
                entity_create = EntityCreate(**entity_data)

                if existing_entity:
                    # Update existing entity
                    updated_entity = await self.entity_service.update_entity(
                        existing_entity.id, entity_create
                    )
                    entities.append(updated_entity)
                    updated_count += 1
                else:
                    # Create new entity
                    new_entity = await self.entity_service.create_entity(entity_create)
                    entities.append(new_entity)
                    created_count += 1

            except Exception as e:
                logger.error(
                    f"Error processing entity {item.get('name', 'unknown')}: {str(e)}"
                )
                error_count += 1

        return {
            "entities_created": created_count,
            "entities_updated": updated_count,
            "entities_error": error_count,
            "entities_total": len(entities),
            "entities": entities,
        }

    def _extract_value(
        self, data: dict[str, Any], field_spec: str | list[str] | None
    ) -> Any:
        """
        Extract a value from data using field specification.

        Args:
            data: Dict containing source data
            field_spec: Field specification, which can be:
                - String with field name (e.g., "name")
                - String with dot notation for nested fields (e.g., "website.url")
                - List of field names to try in order (e.g., ["ward_phone", "city_hall_phone"])

        Returns:
            Extracted value or None if not found
        """
        if field_spec is None:
            return None

        # Handle list of fields to try in order
        if isinstance(field_spec, list):
            for field in field_spec:
                value = self._extract_value(data, field)
                if value:
                    return value
            return None

        # Handle dot notation for nested fields
        if "." in field_spec:
            parts = field_spec.split(".", 1)
            parent = data.get(parts[0])
            if parent:
                if isinstance(parent, dict):
                    return self._extract_value(parent, parts[1])
                elif isinstance(parent, list):
                    # Try to parse the next part as an integer (array index)
                    index_parts = parts[1].split(".", 1)
                    try:
                        index = int(index_parts[0])
                        if 0 <= index < len(parent):
                            if len(index_parts) > 1:
                                # Continue with the rest of the path
                                return self._extract_value(
                                    parent[index], index_parts[1]
                                )
                            else:
                                # Return the value at the index
                                return parent[index]
                    except ValueError:
                        # Not an integer index
                        pass
            return None

        # Handle simple field
        return data.get(field_spec)

    async def validate_import(self, **kwargs: Any) -> bool:
        """Validate entity import parameters."""
        required = ["jurisdiction_name", "entity_type", "title", "mapping"]
        if "data_key" in kwargs:
            required.append("data")
        return all(field in kwargs for field in required)
