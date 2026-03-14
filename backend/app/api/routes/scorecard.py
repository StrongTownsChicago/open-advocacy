"""Scorecard API route — returns cross-project alignment data for a group."""

from fastapi import APIRouter, Depends, HTTPException

from app.models.pydantic.models import ScorecardResponse
from app.services.group_service import GroupService
from app.services.scorecard_service import ScorecardService
from app.services.service_factory import get_group_service, get_scorecard_service

router = APIRouter()


@router.get("/{group_slug}", response_model=ScorecardResponse)
async def get_scorecard(
    group_slug: str,
    scorecard_service: ScorecardService = Depends(get_scorecard_service),
    group_service: GroupService = Depends(get_group_service),
) -> ScorecardResponse:
    """Return a full scorecard for all active projects in a group identified by slug.

    No authentication required — this is a public endpoint.
    Returns 404 if no group matches the slug.
    """
    group = await group_service.find_by_slug(group_slug)
    if group is None:
        raise HTTPException(status_code=404, detail=f"Group '{group_slug}' not found")
    return await scorecard_service.get_scorecard(group.id, group.name)
