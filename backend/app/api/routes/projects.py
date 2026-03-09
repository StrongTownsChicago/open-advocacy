from fastapi import APIRouter, HTTPException, Depends, status
from uuid import UUID

from app.models.pydantic.models import Project, ProjectBase, ProjectStatus, User
from app.services.project_service import ProjectService
from app.services.service_factory import get_project_service
from app.core.auth import get_active_user


router = APIRouter()


@router.get("/", response_model=list[Project])
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    status: ProjectStatus = None,
    group_id: UUID = None,
    project_service: ProjectService = Depends(get_project_service),
):
    """List projects with optional filtering."""
    return await project_service.list_projects(
        skip=skip, limit=limit, status=status, group_id=group_id
    )


@router.get("/by-name/{name}", response_model=Project)
async def get_project_by_name(
    name: str,
    project_service: ProjectService = Depends(get_project_service),
):
    """Get a project by its title/name."""
    project = await project_service.get_project_by_name(name)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/", response_model=Project, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: ProjectBase,
    project_service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_active_user),
):
    """Create a new project."""
    try:
        return await project_service.create_project(project)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{project_id}", response_model=Project)
async def get_project(
    project_id: UUID,
    project_service: ProjectService = Depends(get_project_service),
):
    """Get a project by ID with related jurisdiction and status information."""
    project = await project_service.get_project_with_details(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=Project)
async def update_project(
    project_id: UUID,
    project: ProjectBase,
    project_service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_active_user),
):
    """Update an existing project."""
    try:
        updated_project = await project_service.update_project(project_id, project)
        if not updated_project:
            raise HTTPException(status_code=404, detail="Project not found")
        return updated_project
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{project_id}", response_model=bool)
async def delete_project(
    project_id: UUID,
    project_service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_active_user),
):
    """Delete a project by ID."""
    deleted = await project_service.delete_project(project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")
    return deleted
