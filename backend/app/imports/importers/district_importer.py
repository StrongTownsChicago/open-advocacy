# app/imports/importers/district_importer.py
from uuid import UUID
from typing import Any
import logging

from app.imports.base import DataImporter
from app.services.district_service import DistrictService
from app.services.jurisdiction_service import JurisdictionService
from app.models.pydantic.models import DistrictBase
from app.geo.provider_factory import get_geo_provider

logger = logging.getLogger(__name__)


class DistrictImporter(DataImporter):
    """
    Importer for district data and boundaries.

    Can import district data from tabular data sources or
    from GeoJSON with boundary information.
    """

    def __init__(
        self,
        district_service: DistrictService,
        jurisdiction_service: JurisdictionService,
        geo_provider=None,
    ):
        self.district_service = district_service
        self.jurisdiction_service = jurisdiction_service
        self.geo_provider = geo_provider or get_geo_provider()

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
        jurisdiction_name: str = "",
        data: list[dict[str, Any]] | dict[str, Any] | None = None,
        geojson_data: dict[str, Any] | None = None,
        name_format: str = "District {code}",
        code_field: str = "district_number",
        district_name_property: str | None = None,
        district_name_prefix: str = "",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Import districts from data source, with optional boundary data.

        Args:
            jurisdiction_name: Name of the parent jurisdiction
            data: List of district data dictionaries (for tabular data)
            geojson_data: GeoJSON data (for boundaries)
            name_format: Format string for district names (e.g., "District {code}")
            code_field: Field in data that contains the district code
            district_name_property: Property in GeoJSON that contains district identifier
            district_name_prefix: Prefix to add to district names (e.g., "Ward ", "District ")

        Returns:
            Dict with import results
        """
        # Lookup jurisdiction ID from name
        jurisdiction_id = await self._get_jurisdiction_id(jurisdiction_name)

        # Track results
        created_count = 0
        updated_count = 0
        error_count = 0
        districts: list[Any] = []

        # Check if data is actually GeoJSON
        if isinstance(data, dict) and data.get("type") == "FeatureCollection":
            geojson_data = data
            data = None

        # Handle tabular data import
        if data and isinstance(data, list):
            await self._import_from_tabular_data(
                data=data,
                jurisdiction_id=jurisdiction_id,
                name_format=name_format,
                code_field=code_field,
                created_count=created_count,
                updated_count=updated_count,
                error_count=error_count,
                districts=districts,
            )

        # Handle GeoJSON boundary import
        if geojson_data:
            # Ensure geojson_data is a dict, not a string
            if isinstance(geojson_data, str):
                try:
                    import json

                    geojson_data = json.loads(geojson_data)
                except json.JSONDecodeError:
                    raise ValueError("Invalid GeoJSON string format")

            await self._import_from_geojson(
                geojson_data=geojson_data,
                jurisdiction_id=jurisdiction_id,
                district_name_property=district_name_property or code_field,
                district_name_prefix=district_name_prefix,
                created_count=created_count,
                updated_count=updated_count,
                error_count=error_count,
                districts=districts,
            )

        return {
            "districts_created": created_count,
            "districts_updated": updated_count,
            "districts_error": error_count,
            "districts_total": len(districts),
            "districts": districts,
        }

    async def _import_from_tabular_data(
        self,
        data: list[dict[str, Any]],
        jurisdiction_id: UUID,
        name_format: str,
        code_field: str,
        created_count: int,
        updated_count: int,
        error_count: int,
        districts: list,
    ):
        """Import districts from tabular data."""
        # Get existing districts for lookup
        existing_districts = await self.district_service.list_districts(jurisdiction_id)
        existing_by_code = {d.code: d for d in existing_districts}

        # Process each district
        for item in data:
            try:
                # Extract district code
                code = str(item.get(code_field))
                if not code:
                    logger.warning("Skipping district without code")
                    error_count += 1
                    continue

                # Create district name
                name = name_format.format(code=code)

                # Check if district already exists
                existing_district = existing_by_code.get(code)

                # Create district object
                district_create = DistrictBase(
                    name=name,
                    code=code,
                    jurisdiction_id=jurisdiction_id,
                )

                if existing_district:
                    # Update existing district
                    updated_district = await self.district_service.update_district(
                        existing_district.id, district_create
                    )
                    districts.append(updated_district)
                    updated_count += 1
                else:
                    # Create new district
                    new_district = await self.district_service.create_district(
                        district_create
                    )
                    districts.append(new_district)
                    created_count += 1

            except Exception as e:
                logger.error(
                    f"Error processing district {item.get(code_field, 'unknown')}: {str(e)}"
                )
                error_count += 1

    async def _import_from_geojson(
        self,
        geojson_data: dict[str, Any],
        jurisdiction_id: UUID,
        district_name_property: str,
        district_name_prefix: str,
        created_count: int,
        updated_count: int,
        error_count: int,
        districts: list,
    ):
        """Import districts and boundaries from GeoJSON."""
        # Validate GeoJSON format
        if (
            not isinstance(geojson_data, dict)
            or geojson_data.get("type") != "FeatureCollection"
        ):
            raise ValueError("Invalid GeoJSON: Expected a FeatureCollection")

        features = geojson_data.get("features", [])
        if not features:
            logger.warning("No features found in GeoJSON")
            return

        # Get existing districts for lookup
        existing_districts = await self.district_service.list_districts(jurisdiction_id)
        existing_by_name = {d.name: d for d in existing_districts}
        existing_by_code = {d.code: d for d in existing_districts}

        # Track already processed districts in this import session
        processed_districts = set()

        # Process each feature
        for feature in features:
            try:
                # Extract district number from properties
                properties = feature.get("properties", {})
                district_number = properties.get(district_name_property)
                if not district_number:
                    logger.warning("Skipping feature without district number")
                    error_count += 1
                    continue

                # Create district name and code
                district_name = f"{district_name_prefix}{district_number}"
                district_code = str(district_number)

                # Skip if we've already processed this district in this session
                if district_name in processed_districts:
                    logger.info(f"Skipping duplicate district: {district_name}")
                    continue

                # Add to processed set
                processed_districts.add(district_name)

                # Check if district already exists
                existing_district = existing_by_name.get(
                    district_name
                ) or existing_by_code.get(district_code)

                if existing_district:
                    logger.info(
                        f"District {district_name} already exists, updating boundary"
                    )
                    district_id = existing_district.id

                    # Update boundary in geo provider
                    await self.geo_provider.store_district_boundary(
                        district_id, feature
                    )
                    districts.append(existing_district)
                    updated_count += 1
                else:
                    logger.info(f"Creating new district: {district_name}")

                    # Create district object
                    district_data = DistrictBase(
                        name=district_name,
                        code=district_code,
                        jurisdiction_id=jurisdiction_id,
                    )

                    # Create district in database
                    new_district = await self.district_service.create_district(
                        district_data
                    )

                    # Store boundary in geo provider
                    await self.geo_provider.store_district_boundary(
                        new_district.id, feature
                    )

                    districts.append(new_district)
                    created_count += 1

            except Exception as e:
                logger.error(f"Error processing district feature: {str(e)}")
                error_count += 1

    async def validate_import(self, **kwargs: Any) -> bool:
        """Validate district import parameters."""
        if "jurisdiction_name" not in kwargs:
            logger.error(f"Jurisdiction name not in kwargs: {kwargs}")
            return False

        return True
