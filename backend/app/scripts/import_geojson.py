import argparse
import asyncio
import json
from uuid import UUID

from app.geo.provider_factory import get_geo_provider


async def import_boundary(file_path: str, jurisdiction_id: UUID):
    """Import GeoJSON file as boundary for a jurisdiction"""

    # Get geographic provider
    geo_provider = get_geo_provider()

    # Read GeoJSON file
    try:
        with open(file_path, "r") as f:
            geojson_data = json.load(f)
    except Exception as e:
        print(f"Error reading GeoJSON file: {str(e)}")
        return False

    # Store in database
    success = await geo_provider.store_district_boundary(jurisdiction_id, geojson_data)

    return success


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import GeoJSON boundary")
    parser.add_argument("file", help="Path to GeoJSON file")
    parser.add_argument("jurisdiction_id", help="UUID of jurisdiction")

    args = parser.parse_args()

    asyncio.run(import_boundary(args.file, UUID(args.jurisdiction_id)))
