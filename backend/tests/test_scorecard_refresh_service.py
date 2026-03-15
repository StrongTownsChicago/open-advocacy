"""Unit tests for scorecard_refresh_service.run_scorecard_refresh()."""

from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.pydantic.models import EntityStatus
from app.services.entity_service import EntityService
from app.services.jurisdiction_service import JurisdictionService
from app.services.project_service import ProjectService
from app.services.status_service import StatusService
from tests.factories import make_entity, make_jurisdiction, make_project

# ---------------------------------------------------------------------------
# Sample ELMS matter data (one vote + one sponsorship project on same GUID)
# ---------------------------------------------------------------------------

_JURISDICTION_ID = uuid4()
_PROJECT_VOTE_ID = uuid4()
_PROJECT_SPONSOR_ID = uuid4()

_ENTITY_A_ID = uuid4()
_ENTITY_B_ID = uuid4()

_SAMPLE_MATTER: dict[str, Any] = {
    "matterId": "54028B60-C4FC-EE11-A1FE-001DD804AF4C",
    "sponsors": [
        {"sponsorName": "Hadden, Maria", "sponsorType": "CoSponsor", "personId": "aaa"},
    ],
    "actions": [
        {
            "actionName": "Passed",
            "actionByName": "City Council",
            "votes": [
                {"voterName": "Hadden, Maria", "vote": "Yea", "personId": "aaa"},
                {"voterName": "La Spata, Daniel", "vote": "Nay", "personId": "bbb"},
            ],
        }
    ],
}

# Two project definitions that share the ADU matter GUID (one vote, one sponsorship)
_TEST_PROJECTS = [
    {
        "base_slug": "adu-citywide-vote",
        "title": "ADU Citywide Expansion — Vote",
        "description": "Test",
        "matter_guid": "54028B60-C4FC-EE11-A1FE-001DD804AF4C",
        "import_type": "vote",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": {
            "solid_approval": "Voted Yes",
            "solid_disapproval": "Voted No",
            "neutral": "Absent/Not Voting",
            "unknown": "Not in Office",
        },
    },
    {
        "base_slug": "adu-citywide-sponsorship",
        "title": "ADU Citywide Expansion — Cosponsors",
        "description": "Test",
        "matter_guid": "54028B60-C4FC-EE11-A1FE-001DD804AF4C",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": {
            "solid_approval": "Cosponsored",
            "neutral": "Not a Cosponsor",
            "unknown": "Not in Office",
        },
    },
]

_TEST_GROUP_CONFIG = [
    {
        "name": "Strong Towns Chicago",
        "description": "Test group",
        "base_slugs": {"adu-citywide-vote", "adu-citywide-sponsorship"},
        "slug_prefix": "",
    },
]


def _make_services(
    entities: list | None = None,
    jurisdiction_name: str | None = "Chicago City Council",
    project_by_slug: dict | None = None,
) -> tuple[
    EntityService, JurisdictionService, ProjectService, StatusService, MagicMock
]:
    """Build mock services with sensible defaults.

    Returns a 5-tuple: (entity_svc, jurisdiction_svc, project_svc, status_svc, status_mock).
    status_mock is the raw MagicMock so tests can inspect call_args_list without mypy errors.
    """
    jurisdiction = (
        make_jurisdiction(id=_JURISDICTION_ID, name="Chicago City Council")
        if jurisdiction_name
        else None
    )

    entity_list = entities or [
        make_entity(
            id=_ENTITY_A_ID,
            name="Maria Hadden",
            jurisdiction_id=_JURISDICTION_ID,
        ),
        make_entity(
            id=_ENTITY_B_ID,
            name="Daniel La Spata",
            jurisdiction_id=_JURISDICTION_ID,
        ),
    ]

    entity_service = MagicMock(spec=EntityService)
    entity_service.list_entities = AsyncMock(return_value=entity_list)

    jurisdiction_service = MagicMock(spec=JurisdictionService)
    jurisdiction_service.find_by_name = AsyncMock(return_value=jurisdiction)

    project_service = MagicMock(spec=ProjectService)

    _project_by_slug = project_by_slug or {
        "adu-citywide-vote": make_project(
            id=_PROJECT_VOTE_ID, slug="adu-citywide-vote"
        ),
        "adu-citywide-sponsorship": make_project(
            id=_PROJECT_SPONSOR_ID, slug="adu-citywide-sponsorship"
        ),
    }
    project_service.get_project_by_slug = AsyncMock(
        side_effect=lambda slug: _project_by_slug.get(slug)
    )

    # Use plain MagicMock (no spec) so call_args_list is accessible without mypy complaints
    status_mock = MagicMock()
    status_mock.create_status_record = AsyncMock(return_value=None)

    return (
        cast(EntityService, entity_service),
        cast(JurisdictionService, jurisdiction_service),
        cast(ProjectService, project_service),
        cast(StatusService, status_mock),
        status_mock,
    )


# ---------------------------------------------------------------------------
# Helpers for patching scorecard project definitions
# ---------------------------------------------------------------------------

_PATCH_PROJECTS = "app.services.scorecard_refresh_service.ALL_SCORECARD_PROJECTS"
_PATCH_GROUP_CONFIG = "app.services.scorecard_refresh_service.GROUP_CONFIG"


@pytest.mark.asyncio
async def test_refresh_returns_correct_shape() -> None:
    """run_scorecard_refresh returns a dict with 'updated' and 'errors' keys."""
    from app.services.scorecard_refresh_service import run_scorecard_refresh

    entity_service, jurisdiction_service, project_service, status_service, _ = (
        _make_services()
    )

    with (
        patch(_PATCH_PROJECTS, _TEST_PROJECTS),
        patch(_PATCH_GROUP_CONFIG, _TEST_GROUP_CONFIG),
        patch(
            "app.services.scorecard_refresh_service._fetch_matter",
            new=AsyncMock(
                return_value=("54028B60-C4FC-EE11-A1FE-001DD804AF4C", _SAMPLE_MATTER)
            ),
        ),
    ):
        result = await run_scorecard_refresh(
            entity_service=entity_service,
            jurisdiction_service=jurisdiction_service,
            project_service=project_service,
            status_service=status_service,
        )

    assert "updated" in result
    assert "errors" in result
    assert isinstance(result["updated"], int)
    assert isinstance(result["errors"], int)


@pytest.mark.asyncio
async def test_refresh_updated_count_equals_entities_times_projects() -> None:
    """With 2 entities and 2 projects, updated count should be 4."""
    from app.services.scorecard_refresh_service import run_scorecard_refresh

    entity_service, jurisdiction_service, project_service, status_service, _ = (
        _make_services()
    )

    with (
        patch(_PATCH_PROJECTS, _TEST_PROJECTS),
        patch(_PATCH_GROUP_CONFIG, _TEST_GROUP_CONFIG),
        patch(
            "app.services.scorecard_refresh_service._fetch_matter",
            new=AsyncMock(
                return_value=("54028B60-C4FC-EE11-A1FE-001DD804AF4C", _SAMPLE_MATTER)
            ),
        ),
    ):
        result = await run_scorecard_refresh(
            entity_service=entity_service,
            jurisdiction_service=jurisdiction_service,
            project_service=project_service,
            status_service=status_service,
        )

    assert result["updated"] == 4  # 2 entities × 2 projects
    assert result["errors"] == 0


@pytest.mark.asyncio
async def test_refresh_skips_project_when_slug_not_in_db() -> None:
    """Missing project slug increments errors and skips upsert for that project."""
    from app.services.scorecard_refresh_service import run_scorecard_refresh

    # Only the vote project exists in DB; sponsorship project is missing
    project_by_slug = {
        "adu-citywide-vote": make_project(
            id=_PROJECT_VOTE_ID, slug="adu-citywide-vote"
        ),
    }
    entity_service, jurisdiction_service, project_service, status_service, _ = (
        _make_services(project_by_slug=project_by_slug)
    )

    with (
        patch(_PATCH_PROJECTS, _TEST_PROJECTS),
        patch(_PATCH_GROUP_CONFIG, _TEST_GROUP_CONFIG),
        patch(
            "app.services.scorecard_refresh_service._fetch_matter",
            new=AsyncMock(
                return_value=("54028B60-C4FC-EE11-A1FE-001DD804AF4C", _SAMPLE_MATTER)
            ),
        ),
    ):
        result = await run_scorecard_refresh(
            entity_service=entity_service,
            jurisdiction_service=jurisdiction_service,
            project_service=project_service,
            status_service=status_service,
        )

    # Only 2 entities × 1 project upserted; 1 error for missing sponsorship project
    assert result["updated"] == 2
    assert result["errors"] == 1


@pytest.mark.asyncio
async def test_refresh_raises_value_error_when_jurisdiction_missing() -> None:
    """ValueError is raised if Chicago City Council jurisdiction is not found."""
    from app.services.scorecard_refresh_service import run_scorecard_refresh

    entity_service, jurisdiction_service, project_service, status_service, _ = (
        _make_services(jurisdiction_name=None)
    )

    with (
        patch(_PATCH_PROJECTS, _TEST_PROJECTS),
        patch(_PATCH_GROUP_CONFIG, _TEST_GROUP_CONFIG),
    ):
        with pytest.raises(
            ValueError, match="Chicago City Council jurisdiction not found"
        ):
            await run_scorecard_refresh(
                entity_service=entity_service,
                jurisdiction_service=jurisdiction_service,
                project_service=project_service,
                status_service=status_service,
            )


@pytest.mark.asyncio
async def test_refresh_counts_elms_fetch_error_as_errors() -> None:
    """When _fetch_matter returns None for a GUID, projects for that GUID get errors."""
    from app.services.scorecard_refresh_service import run_scorecard_refresh

    entity_service, jurisdiction_service, project_service, status_service, _ = (
        _make_services()
    )

    with (
        patch(_PATCH_PROJECTS, _TEST_PROJECTS),
        patch(_PATCH_GROUP_CONFIG, _TEST_GROUP_CONFIG),
        patch(
            "app.services.scorecard_refresh_service._fetch_matter",
            new=AsyncMock(return_value=("54028B60-C4FC-EE11-A1FE-001DD804AF4C", None)),
        ),
    ):
        result = await run_scorecard_refresh(
            entity_service=entity_service,
            jurisdiction_service=jurisdiction_service,
            project_service=project_service,
            status_service=status_service,
        )

    # Both projects (vote + sponsorship) share the failed GUID — 2 fetch_errors
    assert result["errors"] >= 2


@pytest.mark.asyncio
async def test_refresh_applies_neutral_as_default_for_sponsorship() -> None:
    """Entity absent from sponsorship data gets NEUTRAL on the sponsorship project."""
    from app.services.scorecard_refresh_service import run_scorecard_refresh

    # Use only the sponsorship project so we can check the specific entity
    sponsorship_only_projects = [_TEST_PROJECTS[1]]  # adu-citywide-sponsorship
    sponsorship_only_group_config = [
        {
            "name": "Strong Towns Chicago",
            "description": "Test group",
            "base_slugs": {"adu-citywide-sponsorship"},
            "slug_prefix": "",
        }
    ]

    # Matter with NO sponsors — entity B is not a sponsor
    matter_no_sponsors: dict[str, Any] = {
        "matterId": "54028B60-C4FC-EE11-A1FE-001DD804AF4C",
        "sponsors": [],
        "actions": [],
    }

    (
        entity_service,
        jurisdiction_service,
        project_service,
        status_service,
        status_mock,
    ) = _make_services(
        project_by_slug={
            "adu-citywide-sponsorship": make_project(
                id=_PROJECT_SPONSOR_ID, slug="adu-citywide-sponsorship"
            )
        }
    )

    with (
        patch(_PATCH_PROJECTS, sponsorship_only_projects),
        patch(_PATCH_GROUP_CONFIG, sponsorship_only_group_config),
        patch(
            "app.services.scorecard_refresh_service._fetch_matter",
            new=AsyncMock(
                return_value=(
                    "54028B60-C4FC-EE11-A1FE-001DD804AF4C",
                    matter_no_sponsors,
                )
            ),
        ),
    ):
        await run_scorecard_refresh(
            entity_service=entity_service,
            jurisdiction_service=jurisdiction_service,
            project_service=project_service,
            status_service=status_service,
        )

    # Both entities are absent from sponsors → both should be NEUTRAL
    calls = status_mock.create_status_record.call_args_list
    assert len(calls) == 2
    for call in calls:
        record = call.args[0]
        assert record.status == EntityStatus.NEUTRAL


@pytest.mark.asyncio
async def test_refresh_applies_unknown_for_entity_absent_from_vote_roll_call() -> None:
    """Entity absent from the vote roll call gets UNKNOWN on the paired sponsorship project."""
    from app.services.scorecard_refresh_service import run_scorecard_refresh

    # Vote matter includes only entity A (maria hadden); entity B (daniel la spata) is absent
    matter_partial_vote: dict[str, Any] = {
        "matterId": "54028B60-C4FC-EE11-A1FE-001DD804AF4C",
        "sponsors": [
            {
                "sponsorName": "Hadden, Maria",
                "sponsorType": "CoSponsor",
                "personId": "aaa",
            },
        ],
        "actions": [
            {
                "actionName": "Passed",
                "actionByName": "City Council",
                "votes": [
                    # Only entity A voted — entity B was not in office
                    {"voterName": "Hadden, Maria", "vote": "Yea", "personId": "aaa"},
                ],
            }
        ],
    }

    (
        entity_service,
        jurisdiction_service,
        project_service,
        status_service,
        status_mock,
    ) = _make_services()

    with (
        patch(_PATCH_PROJECTS, _TEST_PROJECTS),
        patch(_PATCH_GROUP_CONFIG, _TEST_GROUP_CONFIG),
        patch(
            "app.services.scorecard_refresh_service._fetch_matter",
            new=AsyncMock(
                return_value=(
                    "54028B60-C4FC-EE11-A1FE-001DD804AF4C",
                    matter_partial_vote,
                )
            ),
        ),
    ):
        await run_scorecard_refresh(
            entity_service=entity_service,
            jurisdiction_service=jurisdiction_service,
            project_service=project_service,
            status_service=status_service,
        )

    # Find the call for entity B on the sponsorship project
    calls = status_mock.create_status_record.call_args_list
    # 2 entities × 2 projects = 4 calls
    assert len(calls) == 4

    # Collect statuses for sponsorship project (project id = _PROJECT_SPONSOR_ID)
    sponsorship_statuses = {
        call.args[0].entity_id: call.args[0].status
        for call in calls
        if call.args[0].project_id == _PROJECT_SPONSOR_ID
    }
    # Entity B absent from vote → UNKNOWN for sponsorship
    assert sponsorship_statuses[_ENTITY_B_ID] == EntityStatus.UNKNOWN
    # Entity A was in the vote roll call → uses sponsorship lookup (SOLID_APPROVAL as a sponsor)
    assert sponsorship_statuses[_ENTITY_A_ID] == EntityStatus.SOLID_APPROVAL


@pytest.mark.asyncio
async def test_refresh_applies_correct_vote_status() -> None:
    """Vote statuses: Yea → SOLID_APPROVAL, Nay → SOLID_DISAPPROVAL."""
    from app.services.scorecard_refresh_service import run_scorecard_refresh

    vote_only_projects = [_TEST_PROJECTS[0]]  # adu-citywide-vote only
    vote_only_group_config = [
        {
            "name": "Strong Towns Chicago",
            "description": "Test group",
            "base_slugs": {"adu-citywide-vote"},
            "slug_prefix": "",
        }
    ]

    (
        entity_service,
        jurisdiction_service,
        project_service,
        status_service,
        status_mock,
    ) = _make_services(
        project_by_slug={
            "adu-citywide-vote": make_project(
                id=_PROJECT_VOTE_ID, slug="adu-citywide-vote"
            )
        }
    )

    with (
        patch(_PATCH_PROJECTS, vote_only_projects),
        patch(_PATCH_GROUP_CONFIG, vote_only_group_config),
        patch(
            "app.services.scorecard_refresh_service._fetch_matter",
            new=AsyncMock(
                return_value=("54028B60-C4FC-EE11-A1FE-001DD804AF4C", _SAMPLE_MATTER)
            ),
        ),
    ):
        await run_scorecard_refresh(
            entity_service=entity_service,
            jurisdiction_service=jurisdiction_service,
            project_service=project_service,
            status_service=status_service,
        )

    calls = status_mock.create_status_record.call_args_list
    assert len(calls) == 2

    statuses_by_entity = {call.args[0].entity_id: call.args[0].status for call in calls}
    assert statuses_by_entity[_ENTITY_A_ID] == EntityStatus.SOLID_APPROVAL
    assert statuses_by_entity[_ENTITY_B_ID] == EntityStatus.SOLID_DISAPPROVAL
