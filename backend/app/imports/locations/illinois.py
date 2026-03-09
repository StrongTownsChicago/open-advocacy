from typing import Any
import os
from pathlib import Path

from app.imports.locations.base import LocationConfig
from app.imports.sources.openstates import IllinoisLegislatorsDataSource
from app.imports.sources.geojson import GeoJSONDataSource
from app.imports.importers.jurisdiction_importer import JurisdictionImporter
from app.imports.importers.district_importer import DistrictImporter
from app.imports.importers.entity_importer import EntityImporter
from app.services.service_factory import (
    get_cached_jurisdiction_service,
    get_cached_district_service,
    get_cached_entity_service,
)
from app.core.config import settings


class IllinoisLocationConfig(LocationConfig):
    """Configuration for Illinois data imports."""

    def __init__(
        self,
        openstates_api_key: str | None = None,
        house_geojson_path: str | None = None,
        senate_geojson_path: str | None = None,
    ):
        resolved_key = openstates_api_key or settings.OPENSTATES_API_KEY
        if not resolved_key:
            raise ValueError("OpenStates API key is required")
        self.openstates_api_key: str = resolved_key

        # Configure file paths
        base_dir = Path(settings.DATA_DIR or "data")
        self.house_geojson_path = house_geojson_path or os.path.join(
            base_dir, "il_2020_state_lower_2021-09-24.json"
        )
        self.senate_geojson_path = senate_geojson_path or os.path.join(
            base_dir, "il_2020_state_upper_2021-09-24.json"
        )

    @property
    def name(self) -> str:
        return "Illinois"

    @property
    def description(self) -> str:
        return "State of Illinois with House and Senate districts and legislators"

    @property
    def import_steps(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "Import Illinois House jurisdiction",
                "importer": "jurisdiction_importer",
                "config": {
                    "name": "Illinois House of Representatives",
                    "description": "Lower chamber of the Illinois General Assembly consisting of 118 representatives",
                    "level": "state_house",
                },
            },
            {
                "name": "Import Illinois Senate jurisdiction",
                "importer": "jurisdiction_importer",
                "config": {
                    "name": "Illinois State Senate",
                    "description": "Upper chamber of the Illinois General Assembly consisting of 59 senators",
                    "level": "state_senate",
                },
            },
            {
                "name": "Import Illinois House GeoJSON",
                "importer": "district_importer",
                "data_source": "house_geojson",
                "config": {
                    "jurisdiction_name": "Illinois House of Representatives",
                    "district_name_property": "Name",
                    "district_name_prefix": "IL House District ",
                },
            },
            {
                "name": "Import Illinois Senate GeoJSON",
                "importer": "district_importer",
                "data_source": "senate_geojson",
                "config": {
                    "jurisdiction_name": "Illinois State Senate",
                    "district_name_property": "Name",
                    "district_name_prefix": "IL Senate District ",
                },
            },
            {
                "name": "Import Illinois House Representatives",
                "importer": "entity_importer",
                "data_source": "legislators",
                "config": {
                    "data_key": "house",
                    "jurisdiction_name": "Illinois House of Representatives",
                    "entity_type": "state_representative",
                    "title": "State Representative",
                    "mapping": {
                        "name": "name",
                        "district_code": "current_role.district",
                        "email": "email",
                        "phone": ["offices.0.voice", "offices.1.voice"],
                        "website": ["links.0.url", "links.1.url"],
                        "address": ["offices.0.address", "offices.1.address"],
                        "image_url": "image",
                    },
                },
            },
            {
                "name": "Import Illinois Senators",
                "importer": "entity_importer",
                "data_source": "legislators",
                "config": {
                    "data_key": "senate",
                    "jurisdiction_name": "Illinois State Senate",
                    "entity_type": "state_senator",
                    "title": "State Senator",
                    "mapping": {
                        "name": "name",
                        "district_code": "current_role.district",
                        "email": "email",
                        "phone": ["offices.0.voice", "offices.1.voice"],
                        "website": ["links.0.url", "links.1.url"],
                        "address": ["offices.0.address", "offices.1.address"],
                        "image_url": "image",
                    },
                },
            },
        ]

    async def get_importers(self) -> dict[str, Any]:
        """Get configured importers for Illinois."""
        jurisdiction_service = get_cached_jurisdiction_service()
        district_service = get_cached_district_service()
        entity_service = get_cached_entity_service()

        legislators_data_source = IllinoisLegislatorsDataSource(
            api_key=self.openstates_api_key
        )

        return {
            "importers": {
                "jurisdiction_importer": JurisdictionImporter(jurisdiction_service),
                "district_importer": DistrictImporter(
                    district_service, jurisdiction_service
                ),
                "entity_importer": EntityImporter(
                    entity_service, district_service, jurisdiction_service
                ),
            },
            "data_sources": {
                "legislators": legislators_data_source,
                "house_geojson": GeoJSONDataSource(file_path=self.house_geojson_path),
                "senate_geojson": GeoJSONDataSource(file_path=self.senate_geojson_path),
            },
        }
