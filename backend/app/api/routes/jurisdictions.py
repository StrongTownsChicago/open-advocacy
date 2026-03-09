from fastapi import APIRouter, HTTPException, Depends
from uuid import UUID

from app.models.pydantic.models import Jurisdiction, JurisdictionBase, User
from app.services.jurisdiction_service import JurisdictionService
from app.services.service_factory import get_jurisdiction_service
from app.core.auth import get_active_user
from app.services.district_service import DistrictService
from app.services.service_factory import get_district_service

router = APIRouter()


@router.get("/", response_model=list[Jurisdiction])
async def list_jurisdictions(
    skip: int = 0,
    limit: int = 100,
    jurisdiction_service: JurisdictionService = Depends(get_jurisdiction_service),
):
    """List all jurisdictions."""
    return await jurisdiction_service.list_jurisdictions(skip=skip, limit=limit)


@router.post("/", response_model=Jurisdiction)
async def create_jurisdiction(
    jurisdiction: JurisdictionBase,
    jurisdiction_service: JurisdictionService = Depends(get_jurisdiction_service),
    current_user: User = Depends(get_active_user),
):
    """Create a new jurisdiction."""
    return await jurisdiction_service.create_jurisdiction(jurisdiction)


@router.get("/{jurisdiction_id}", response_model=Jurisdiction)
async def get_jurisdiction(
    jurisdiction_id: UUID,
    jurisdiction_service: JurisdictionService = Depends(get_jurisdiction_service),
):
    """Get a jurisdiction by ID."""
    jurisdiction = await jurisdiction_service.get_jurisdiction(jurisdiction_id)
    if not jurisdiction:
        raise HTTPException(status_code=404, detail="Jurisdiction not found")
    return jurisdiction


@router.get("/{jurisdiction_id}/geojson", response_model=dict)
async def get_all_districts_geojson(
    jurisdiction_id: UUID,
    district_service: DistrictService = Depends(get_district_service),
):
    """
    Get all district boundaries (GeoJSON) for a jurisdiction.
    Returns: {district_id: boundary_geojson}
    """
    districts = await district_service.list_districts(jurisdiction_id=jurisdiction_id)
    return {d.name: d.boundary for d in districts if d.boundary}


@router.put("/{jurisdiction_id}", response_model=Jurisdiction)
async def update_jurisdiction(
    jurisdiction_id: UUID,
    jurisdiction: JurisdictionBase,
    jurisdiction_service: JurisdictionService = Depends(get_jurisdiction_service),
    current_user: User = Depends(get_active_user),
):
    """Update an existing jurisdiction."""
    existing_jurisdiction = await jurisdiction_service.get_jurisdiction(jurisdiction_id)
    if not existing_jurisdiction:
        raise HTTPException(status_code=404, detail="Jurisdiction not found")

    return await jurisdiction_service.update_jurisdiction(jurisdiction_id, jurisdiction)


@router.delete("/{jurisdiction_id}", response_model=bool)
async def delete_jurisdiction(
    jurisdiction_id: UUID,
    jurisdiction_service: JurisdictionService = Depends(get_jurisdiction_service),
    current_user: User = Depends(get_active_user),
):
    """Delete a jurisdiction by ID."""
    existing_jurisdiction = await jurisdiction_service.get_jurisdiction(jurisdiction_id)
    if not existing_jurisdiction:
        raise HTTPException(status_code=404, detail="Jurisdiction not found")

    return await jurisdiction_service.delete_jurisdiction(jurisdiction_id)
