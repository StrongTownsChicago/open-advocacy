"""Admin route for refreshing scorecard data from the eLMS API."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import get_super_admin_user
from app.models.pydantic.models import User
from app.services.entity_service import EntityService
from app.services.jurisdiction_service import JurisdictionService
from app.services.project_service import ProjectService
from app.services.scorecard_refresh_service import run_scorecard_refresh
from app.services.service_factory import (
    get_entity_service,
    get_jurisdiction_service,
    get_project_service,
    get_status_service,
)
from app.services.status_service import StatusService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/refresh", response_model=dict[str, Any])
async def refresh_scorecard_data(
    current_user: User = Depends(get_super_admin_user),
    entity_service: EntityService = Depends(get_entity_service),
    jurisdiction_service: JurisdictionService = Depends(get_jurisdiction_service),
    project_service: ProjectService = Depends(get_project_service),
    status_service: StatusService = Depends(get_status_service),
) -> dict[str, Any]:
    """Fetch fresh scorecard data and upsert EntityStatusRecords.

    Only accessible by super admins. Triggers a live fetch from the Chicago
    City Clerk eLMS API and the OpenStates API, and updates all scorecard
    project status records.

    Returns:
        {"updated": int, "errors": int}
    """
    try:
        result = await run_scorecard_refresh(
            entity_service=entity_service,
            jurisdiction_service=jurisdiction_service,
            project_service=project_service,
            status_service=status_service,
        )
        return result
    except Exception as e:
        logger.exception("Scorecard refresh failed")
        raise HTTPException(status_code=500, detail=f"Scorecard refresh failed: {e}")
