import asyncio
import json
from uuid import UUID
import sys

from app.db.dependencies import get_jurisdictions_provider, get_districts_provider
from app.models.pydantic.models import DistrictBase, Jurisdiction
from app.geo.provider_factory import get_geo_provider


async def import_chicago_wards(
    file_path: str = "app/data/chicago-wards.geojson",
    jurisdiction_id: UUID | None = None,
):
    """
    Import Chicago wards from a GeoJSON file into District model

    Args:
        file_path: Path to GeoJSON file with ward boundaries
        jurisdiction_id: Optional parent jurisdiction ID (City of Chicago)
    """
    # Get providers
    jurisdictions_provider = get_jurisdictions_provider()
    districts_provider = get_districts_provider()
    geo_provider = get_geo_provider()

    jurisdiction: Jurisdiction | None = None

    # Verify jurisdiction exists
    if jurisdiction_id:
        jurisdiction = await jurisdictions_provider.get(jurisdiction_id)
        if not jurisdiction:
            print(f"Jurisdiction with ID {jurisdiction_id} not found")

    if not jurisdiction:
        jurisdiction_list: list[Jurisdiction] = await jurisdictions_provider.filter(
            name="Chicago City Council"
        )
        jurisdiction = jurisdiction_list[0]
        jurisdiction_id = jurisdiction.id

    # Read GeoJSON file
    try:
        with open(file_path, "r") as f:
            geojson_data = json.load(f)
    except Exception as e:
        print(f"Error reading GeoJSON file: {str(e)}")
        return False

    # Validate GeoJSON
    if (
        not isinstance(geojson_data, dict)
        or geojson_data.get("type") != "FeatureCollection"
    ):
        print("Invalid GeoJSON: Expected a FeatureCollection")
        return False

    features = geojson_data.get("features", [])
    if not features:
        print("No features found in GeoJSON")
        return False

    # Process each ward
    for feature in features:
        if not feature.get("properties") or "ward" not in feature["properties"]:
            print("Skipping feature without ward number")
            continue

        ward_num = feature["properties"]["ward"]
        ward_name = f"Ward {ward_num}"

        # Check if district already exists
        existing_districts = await districts_provider.filter(name=ward_name)

        if existing_districts:
            print(f"Ward {ward_num} already exists, updating boundary")
            district_id = existing_districts[0].id
            # Update boundary
            await geo_provider.store_district_boundary(district_id, feature)
        else:
            print(f"Creating new ward: {ward_name}")
            # Create new district for ward
            if jurisdiction_id is None:
                raise ValueError("jurisdiction_id is required to create districts")
            new_district = DistrictBase(
                name=ward_name,
                code=str(ward_num),
                jurisdiction_id=jurisdiction_id,
            )

            created_district = await districts_provider.create(new_district)

            # Store boundary
            await geo_provider.store_district_boundary(created_district.id, feature)

    print(f"Processed {len(features)} wards")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_chicago_wards.py <geojson_file> [jurisdiction_id]")
        sys.exit(1)

    file_path = sys.argv[1]
    parent_id = UUID(sys.argv[2]) if len(sys.argv) > 2 else None

    asyncio.run(import_chicago_wards(file_path, parent_id))
