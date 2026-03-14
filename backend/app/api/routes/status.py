from fastapi import APIRouter, HTTPException, Depends, status
from uuid import UUID

from app.models.pydantic.models import EntityStatusRecord, User
from app.services.status_service import StatusService
from app.services.service_factory import get_status_service
from app.core.auth import get_active_user
from app.exceptions import NotFoundError


router = APIRouter()


@router.get("/", response_model=list[EntityStatusRecord] | None)
async def list_status_records(
    project_id: UUID | None = None,
    entity_id: UUID | None = None,
    status_service: StatusService = Depends(get_status_service),
):
    """List status records with optional filtering."""
    return await status_service.list_status_records(
        project_id=project_id, entity_id=entity_id
    )


@router.post("/", response_model=EntityStatusRecord)
async def create_status_record(
    status_record: EntityStatusRecord,
    status_service: StatusService = Depends(get_status_service),
    current_user: User = Depends(get_active_user),
):
    """Create a new status record."""
    try:
        return await status_service.create_status_record(status_record)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{record_id}", response_model=EntityStatusRecord)
async def get_status_record(
    record_id: UUID,
    status_service: StatusService = Depends(get_status_service),
):
    """Get a status record by ID."""
    record = await status_service.get_status_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Status record not found")
    return record


@router.put("/{record_id}", response_model=EntityStatusRecord)
async def update_status_record(
    record_id: UUID,
    status_record: EntityStatusRecord,
    status_service: StatusService = Depends(get_status_service),
    current_user: User = Depends(get_active_user),
):
    """Update an existing status record."""
    updated_record = await status_service.update_status_record(record_id, status_record)
    if not updated_record:
        raise HTTPException(status_code=404, detail="Status record not found")
    return updated_record


@router.delete("/{record_id}", response_model=bool)
async def delete_status_record(
    record_id: UUID,
    status_service: StatusService = Depends(get_status_service),
    current_user: User = Depends(get_active_user),
):
    """Delete a status record by ID."""
    deleted = await status_service.delete_status_record(record_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Status record not found")
    return deleted
