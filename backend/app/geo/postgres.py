from typing import List, Dict, Any
from uuid import UUID
import json
from sqlalchemy import text

from app.geo.base import GeoProvider


class PostgresGeoProvider(GeoProvider):
    """PostgreSQL implementation of geographic operations using PostGIS"""

    async def districts_containing_point(self, lat: float, lon: float) -> List[UUID]:
        """
        Find all district IDs that contain the given point using PostGIS
        """
        async with self.session_factory() as session:
            # Use native PostGIS functions for optimal performance
            query = text("""
                SELECT d.id 
                FROM districts d
                WHERE d.boundary IS NOT NULL AND ST_Contains(
                    ST_SetSRID(ST_GeomFromGeoJSON(d.boundary->>'geometry'), 4326),
                    ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)
                )
            """)

            result = await session.execute(query, {"lon": lon, "lat": lat})
            return [row[0] for row in result]

    async def store_district_boundary(
        self, district_id: UUID, geojson: Dict[str, Any]
    ) -> bool:
        """
        Store a boundary for a district, optimizing for PostGIS
        """
        async with self.session_factory() as session:
            # Update the boundary using proper parameter style
            query = text("""
                UPDATE districts
                SET boundary = cast(:geojson AS jsonb)
                WHERE id = :district_id
                RETURNING id
            """)

            result = await session.execute(
                query, {"geojson": json.dumps(geojson), "district_id": str(district_id)}
            )

            await session.commit()
            return result.rowcount > 0

    async def get_district_boundary(self, district_id: UUID) -> Dict[str, Any] | None:
        """
        Get a boundary for a district
        """
        async with self.session_factory() as session:
            query = text("""
                SELECT boundary 
                FROM districts
                WHERE id = :district_id
            """)

            result = await session.execute(query, {"district_id": str(district_id)})

            row = result.fetchone()
            return row[0] if row else None
