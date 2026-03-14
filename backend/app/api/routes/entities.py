from fastapi import APIRouter, HTTPException, Depends, status
from uuid import UUID
from typing import List

from app.models.pydantic.models import Entity, EntityCreate, AddressLookupRequest, User
from app.services.entity_service import EntityService
from app.services.service_factory import get_entity_service
from app.core.auth import get_active_user
from app.exceptions import NotFoundError

router = APIRouter()


@router.get("/", response_model=list[Entity])
async def list_entities(
    jurisdiction_id: UUID,
    entity_service: EntityService = Depends(get_entity_service),
):
    """List entities by jurisdiction."""
    return await entity_service.list_entities(jurisdiction_id=jurisdiction_id)


@router.post("/", response_model=Entity)
async def create_entity(
    entity: EntityCreate,
    entity_service: EntityService = Depends(get_entity_service),
    current_user: User = Depends(get_active_user),
):
    """Create a new entity."""
    try:
        return await entity_service.create_entity(entity)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{entity_id}", response_model=Entity)
async def get_entity(
    entity_id: UUID,
    entity_service: EntityService = Depends(get_entity_service),
):
    """Get an entity by ID."""
    entity = await entity_service.get_entity(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@router.put("/{entity_id}", response_model=Entity)
async def update_entity(
    entity_id: UUID,
    entity: EntityCreate,
    entity_service: EntityService = Depends(get_entity_service),
    current_user: User = Depends(get_active_user),
):
    """Update an existing entity."""
    updated_entity = await entity_service.update_entity(entity_id, entity)
    if not updated_entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return updated_entity


@router.delete("/{entity_id}", response_model=bool)
async def delete_entity(
    entity_id: UUID,
    entity_service: EntityService = Depends(get_entity_service),
    current_user: User = Depends(get_active_user),
):
    """Delete an entity by ID."""
    deleted = await entity_service.delete_entity(entity_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Entity not found")
    return deleted


@router.post("/address_lookup", response_model=List[Entity])
async def lookup_entities_by_address(
    request: AddressLookupRequest,
    entity_service: EntityService = Depends(get_entity_service),
):
    """Look up entities for a given address."""
    try:
        return await entity_service.lookup_entities_by_address(request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
