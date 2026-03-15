"""Unit tests for scripts.import_scorecard_projects."""

import logging
from typing import cast
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.pydantic.models import DashboardConfig, EntityStatus
from app.services.entity_service import EntityService
from app.services.group_service import GroupService
from app.services.jurisdiction_service import JurisdictionService
from app.services.project_service import ProjectService
from app.services.status_service import StatusService
from tests.factories import make_entity, make_group, make_jurisdiction, make_project

# ---------------------------------------------------------------------------
# Shared IDs
# ---------------------------------------------------------------------------

_JURISDICTION_ID = uuid4()
_GROUP_ID = uuid4()
_PROJECT_VOTE_ID = uuid4()
_PROJECT_SPONSOR_ID = uuid4()
_ENTITY_A_ID = uuid4()
_ENTITY_B_ID = uuid4()

# ---------------------------------------------------------------------------
# Minimal project and group definitions for testing
# ---------------------------------------------------------------------------

_VOTE_PROJECT_DEF = {
    "base_slug": "test-vote",
    "title": "Test Vote Project",
    "description": "A test vote",
    "matter_guid": "VOTE-GUID-001",
    "import_type": "vote",
    "preferred_status": EntityStatus.SOLID_APPROVAL,
    "status_labels": {
        "solid_approval": "Voted Yes",
        "solid_disapproval": "Voted No",
        "neutral": "Absent/Not Voting",
        "unknown": "Not in Office",
    },
}

_SPONSOR_PROJECT_DEF = {
    "base_slug": "test-sponsorship",
    "title": "Test Sponsorship Project",
    "description": "A test sponsorship",
    "matter_guid": "VOTE-GUID-001",  # paired with vote
    "import_type": "sponsorship",
    "preferred_status": EntityStatus.SOLID_APPROVAL,
    "status_labels": {
        "solid_approval": "Cosponsored",
        "neutral": "Not a Cosponsor",
        "unknown": "Not in Office",
    },
}

# Group with both vote + sponsorship for the same matter GUID
_TEST_ELMS_PROJECTS = [_VOTE_PROJECT_DEF, _SPONSOR_PROJECT_DEF]

_TEST_GROUP_CONFIG_ELMS = [
    {
        "name": "Test Chicago Group",
        "description": "Test group description",
        "jurisdiction_name": "Chicago City Council",
        "base_slugs": {"test-vote", "test-sponsorship"},
        "slug_prefix": "",
        "data_source": "elms",
        "representative_title": "Alderperson",
    }
]

_IL_SPONSOR_PROJECT_DEF = {
    "base_slug": "il-test-sponsorship",
    "title": "IL Test Sponsorship",
    "description": "An IL test sponsorship",
    "bill_identifier": "SB 9999",
    "chamber": "senate",
    "import_type": "sponsorship",
    "preferred_status": EntityStatus.SOLID_APPROVAL,
    "status_labels": {
        "solid_approval": "Cosponsored",
        "neutral": "Not a Cosponsor",
        "unknown": "Not in Office",
    },
}

_TEST_GROUP_CONFIG_IL = [
    {
        "name": "Test IL Senate Group",
        "description": "Test IL group",
        "jurisdiction_name": "Illinois State Senate",
        "base_slugs": {"il-test-sponsorship"},
        "slug_prefix": "ahil-senate-",
        "data_source": "il_openstates",
        "representative_title": "Senator",
    }
]


# ---------------------------------------------------------------------------
# Service mock factory
# ---------------------------------------------------------------------------


def _make_services(
    entities: list | None = None,
    jurisdiction_name: str | None = "Chicago City Council",
    project_by_slug: dict | None = None,
) -> tuple[
    EntityService,
    JurisdictionService,
    ProjectService,
    GroupService,
    StatusService,
    MagicMock,  # status_mock (raw, for assertions)
    MagicMock,  # project_mock (raw, for assertions)
]:
    jurisdiction = (
        make_jurisdiction(id=_JURISDICTION_ID, name=jurisdiction_name or "")
        if jurisdiction_name
        else None
    )
    entity_list = entities or [
        make_entity(
            id=_ENTITY_A_ID, name="Alice Johnson", jurisdiction_id=_JURISDICTION_ID
        ),
        make_entity(
            id=_ENTITY_B_ID, name="Bob Smith", jurisdiction_id=_JURISDICTION_ID
        ),
    ]

    entity_svc = MagicMock(spec=EntityService)
    entity_svc.list_entities = AsyncMock(return_value=entity_list)

    jurisdiction_svc = MagicMock(spec=JurisdictionService)
    jurisdiction_svc.find_by_name = AsyncMock(return_value=jurisdiction)

    project_svc = MagicMock(spec=ProjectService)
    _project_by_slug: dict = project_by_slug or {}
    project_svc.get_project_by_slug = AsyncMock(
        side_effect=lambda slug: _project_by_slug.get(slug)
    )
    project_svc.create_project = AsyncMock(
        side_effect=lambda pb: make_project(
            slug=pb.slug, dashboard_config=pb.dashboard_config
        )
    )
    project_svc.update_project = AsyncMock(return_value=None)

    group_svc = MagicMock(spec=GroupService)
    group_svc.find_or_create_by_name = AsyncMock(
        return_value=make_group(id=_GROUP_ID, name="Test Chicago Group")
    )

    status_mock = MagicMock()
    status_mock.create_status_record = AsyncMock(return_value=None)

    return (
        cast(EntityService, entity_svc),
        cast(JurisdictionService, jurisdiction_svc),
        cast(ProjectService, project_svc),
        cast(GroupService, group_svc),
        cast(StatusService, status_mock),
        status_mock,
        project_svc,  # raw MagicMock for call assertions
    )


def _patches(
    entity_svc: EntityService,
    jurisdiction_svc: JurisdictionService,
    project_svc: ProjectService,
    group_svc: GroupService,
    status_svc: StatusService,
    *,
    elms_data: dict | None = None,
    il_data: dict | None = None,
    group_config: list | None = None,
    elms_projects: list | None = None,
    il_projects: list | None = None,
) -> list:
    """Build the list of patches needed for import_scorecard_projects tests."""
    ps = [
        patch(
            "scripts.import_scorecard_projects.get_cached_entity_service",
            return_value=entity_svc,
        ),
        patch(
            "scripts.import_scorecard_projects.get_cached_jurisdiction_service",
            return_value=jurisdiction_svc,
        ),
        patch(
            "scripts.import_scorecard_projects.get_cached_project_service",
            return_value=project_svc,
        ),
        patch(
            "scripts.import_scorecard_projects.get_cached_group_service",
            return_value=group_svc,
        ),
        patch(
            "scripts.import_scorecard_projects.get_cached_status_service",
            return_value=status_svc,
        ),
        patch(
            "scripts.import_scorecard_projects.GROUP_CONFIG",
            group_config or _TEST_GROUP_CONFIG_ELMS,
        ),
        patch(
            "scripts.import_scorecard_projects.ALL_SCORECARD_PROJECTS",
            elms_projects or _TEST_ELMS_PROJECTS,
        ),
        patch(
            "scripts.import_scorecard_projects.ALL_IL_SCORECARD_PROJECTS",
            il_projects or [],
        ),
        patch("scripts.import_scorecard_projects.ELMS_SCORECARD_DATA", elms_data or {}),
        patch("scripts.import_scorecard_projects.IL_SCORECARD_DATA", il_data or {}),
    ]
    return ps


# ---------------------------------------------------------------------------
# Tests: _get_entity_status_lookup
# ---------------------------------------------------------------------------


class TestGetEntityStatusLookup:
    def test_elms_returns_lookup_with_enum_values(self) -> None:
        """ELMS cache entries are converted from raw strings to EntityStatus enums."""
        from scripts.import_scorecard_projects import _get_entity_status_lookup

        cache = {
            "alice johnson": "solid_approval",
            "bob smith": "neutral",
        }
        logger = logging.getLogger("test")

        with patch(
            "scripts.import_scorecard_projects.ELMS_SCORECARD_DATA", {"my-slug": cache}
        ):
            result = _get_entity_status_lookup("my-slug", "elms", logger)

        assert result == {
            "alice johnson": EntityStatus.SOLID_APPROVAL,
            "bob smith": EntityStatus.NEUTRAL,
        }

    def test_elms_missing_cache_returns_empty_dict_and_warns(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Missing ELMS slug returns empty dict and logs a warning."""
        from scripts.import_scorecard_projects import _get_entity_status_lookup

        logger = logging.getLogger("test")
        with patch("scripts.import_scorecard_projects.ELMS_SCORECARD_DATA", {}):
            with caplog.at_level(logging.WARNING, logger="test"):
                result = _get_entity_status_lookup("no-such-slug", "elms", logger)

        assert result == {}
        assert "no-such-slug" in caplog.text

    def test_il_openstates_returns_lookup_with_enum_values(self) -> None:
        """IL OpenStates cache entries are converted from raw strings to EntityStatus enums."""
        from scripts.import_scorecard_projects import _get_entity_status_lookup

        cache = {
            "alice johnson": "solid_approval",
            "bob smith": "solid_disapproval",
        }
        logger = logging.getLogger("test")

        with patch(
            "scripts.import_scorecard_projects.IL_SCORECARD_DATA", {"il-slug": cache}
        ):
            result = _get_entity_status_lookup("il-slug", "il_openstates", logger)

        assert result == {
            "alice johnson": EntityStatus.SOLID_APPROVAL,
            "bob smith": EntityStatus.SOLID_DISAPPROVAL,
        }

    def test_il_missing_cache_returns_empty_dict_and_warns(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Missing IL slug returns empty dict and logs a warning."""
        from scripts.import_scorecard_projects import _get_entity_status_lookup

        logger = logging.getLogger("test")
        with patch("scripts.import_scorecard_projects.IL_SCORECARD_DATA", {}):
            with caplog.at_level(logging.WARNING, logger="test"):
                result = _get_entity_status_lookup(
                    "no-such-il-slug", "il_openstates", logger
                )

        assert result == {}
        assert "no-such-il-slug" in caplog.text

    def test_empty_cache_entry_returns_empty_dict(self) -> None:
        """An explicit empty dict in cache returns empty lookup (no enums to convert)."""
        from scripts.import_scorecard_projects import _get_entity_status_lookup

        logger = logging.getLogger("test")
        with patch(
            "scripts.import_scorecard_projects.ELMS_SCORECARD_DATA", {"my-slug": {}}
        ):
            result = _get_entity_status_lookup("my-slug", "elms", logger)

        assert result == {}


# ---------------------------------------------------------------------------
# Tests: _normalize_entity_name
# ---------------------------------------------------------------------------


class TestNormalizeEntityName:
    def test_elms_routes_to_normalize_name(self) -> None:
        """ELMS data source uses the Chicago ELMS normalizer."""
        from scripts.import_scorecard_projects import _normalize_entity_name

        with patch(
            "scripts.import_scorecard_projects.normalize_name",
            return_value="alice johnson",
        ) as mock_norm:
            result = _normalize_entity_name("Alice Johnson (47)", "elms")

        mock_norm.assert_called_once_with("Alice Johnson (47)")
        assert result == "alice johnson"

    def test_il_openstates_routes_to_normalize_il_name(self) -> None:
        """IL OpenStates data source uses the IL normalizer."""
        from scripts.import_scorecard_projects import _normalize_entity_name

        with patch(
            "scripts.import_scorecard_projects.normalize_il_name",
            return_value="alice johnson",
        ) as mock_norm:
            result = _normalize_entity_name("Rep. Alice Johnson", "il_openstates")

        mock_norm.assert_called_once_with("Rep. Alice Johnson")
        assert result == "alice johnson"


# ---------------------------------------------------------------------------
# Tests: import_scorecard_projects (main async function)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_creates_projects_when_none_exist() -> None:
    """Projects are created when they don't already exist in the database."""
    from scripts.import_scorecard_projects import import_scorecard_projects

    (
        entity_svc,
        jurisdiction_svc,
        project_svc,
        group_svc,
        status_svc,
        _,
        project_mock,
    ) = _make_services()

    ps = _patches(entity_svc, jurisdiction_svc, project_svc, group_svc, status_svc)
    for p in ps:
        p.start()
    try:
        await import_scorecard_projects()
    finally:
        for p in reversed(ps):
            p.stop()

    assert project_mock.create_project.call_count == 2  # one vote + one sponsorship
    project_mock.update_project.assert_not_called()


@pytest.mark.asyncio
async def test_finds_existing_projects_without_creating() -> None:
    """When projects already exist, create_project is not called."""
    from scripts.import_scorecard_projects import import_scorecard_projects

    existing = {
        "test-vote": make_project(
            id=_PROJECT_VOTE_ID,
            slug="test-vote",
            dashboard_config=DashboardConfig(
                representative_title="Alderperson",
                status_labels={},
                position=None,
            ),
        ),
        "test-sponsorship": make_project(
            id=_PROJECT_SPONSOR_ID,
            slug="test-sponsorship",
            dashboard_config=DashboardConfig(
                representative_title="Alderperson",
                status_labels={},
                position=None,
            ),
        ),
    }
    (
        entity_svc,
        jurisdiction_svc,
        project_svc,
        group_svc,
        status_svc,
        _,
        project_mock,
    ) = _make_services(project_by_slug=existing)

    ps = _patches(entity_svc, jurisdiction_svc, project_svc, group_svc, status_svc)
    for p in ps:
        p.start()
    try:
        await import_scorecard_projects()
    finally:
        for p in reversed(ps):
            p.stop()

    project_mock.create_project.assert_not_called()


@pytest.mark.asyncio
async def test_updates_project_position_when_changed() -> None:
    """When an existing project has a different position, update_project is called."""
    from scripts.import_scorecard_projects import import_scorecard_projects

    # Project with position=1 in DB, but project_def has no position (None)
    existing = {
        "test-vote": make_project(
            id=_PROJECT_VOTE_ID,
            slug="test-vote",
            dashboard_config=DashboardConfig(
                representative_title="Alderperson",
                status_labels={},
                position=1,  # will differ from project_def which has no "position" key
            ),
        ),
    }

    # Single-project group with no position in definition
    vote_def_no_position = {**_VOTE_PROJECT_DEF}  # has no "position" key → None
    single_project_config = [
        {
            **_TEST_GROUP_CONFIG_ELMS[0],
            "base_slugs": {"test-vote"},
        }
    ]

    (
        entity_svc,
        jurisdiction_svc,
        project_svc,
        group_svc,
        status_svc,
        _,
        project_mock,
    ) = _make_services(project_by_slug=existing)

    ps = _patches(
        entity_svc,
        jurisdiction_svc,
        project_svc,
        group_svc,
        status_svc,
        group_config=single_project_config,
        elms_projects=[vote_def_no_position],
    )
    for p in ps:
        p.start()
    try:
        await import_scorecard_projects()
    finally:
        for p in reversed(ps):
            p.stop()

    project_mock.update_project.assert_called_once()


@pytest.mark.asyncio
async def test_does_not_update_project_when_position_unchanged() -> None:
    """When position matches, update_project is not called."""
    from scripts.import_scorecard_projects import import_scorecard_projects

    # Project with position=None in DB; project_def also has no "position" key
    existing = {
        "test-vote": make_project(
            id=_PROJECT_VOTE_ID,
            slug="test-vote",
            dashboard_config=DashboardConfig(
                representative_title="Alderperson",
                status_labels={},
                position=None,
            ),
        ),
    }

    single_project_config = [
        {
            **_TEST_GROUP_CONFIG_ELMS[0],
            "base_slugs": {"test-vote"},
        }
    ]

    (
        entity_svc,
        jurisdiction_svc,
        project_svc,
        group_svc,
        status_svc,
        _,
        project_mock,
    ) = _make_services(project_by_slug=existing)

    ps = _patches(
        entity_svc,
        jurisdiction_svc,
        project_svc,
        group_svc,
        status_svc,
        group_config=single_project_config,
        elms_projects=[_VOTE_PROJECT_DEF],
    )
    for p in ps:
        p.start()
    try:
        await import_scorecard_projects()
    finally:
        for p in reversed(ps):
            p.stop()

    project_mock.update_project.assert_not_called()


@pytest.mark.asyncio
async def test_skips_group_when_jurisdiction_not_found() -> None:
    """When jurisdiction is not found, the group is skipped (no projects created)."""
    from scripts.import_scorecard_projects import import_scorecard_projects

    (
        entity_svc,
        jurisdiction_svc,
        project_svc,
        group_svc,
        status_svc,
        status_mock,
        project_mock,
    ) = _make_services(
        jurisdiction_name=None  # triggers None return from find_by_name
    )

    ps = _patches(entity_svc, jurisdiction_svc, project_svc, group_svc, status_svc)
    for p in ps:
        p.start()
    try:
        await import_scorecard_projects()
    finally:
        for p in reversed(ps):
            p.stop()

    project_mock.create_project.assert_not_called()
    status_mock.create_status_record.assert_not_called()


@pytest.mark.asyncio
async def test_vote_project_defaults_unmatched_entities_to_unknown() -> None:
    """Entities absent from the vote cache are assigned UNKNOWN (not in office)."""
    from scripts.import_scorecard_projects import import_scorecard_projects

    # Cache is empty — neither entity voted
    elms_data: dict[str, dict] = {"test-vote": {}}

    single_project_config = [
        {
            **_TEST_GROUP_CONFIG_ELMS[0],
            "base_slugs": {"test-vote"},
        }
    ]

    entity_svc, jurisdiction_svc, project_svc, group_svc, status_svc, status_mock, _ = (
        _make_services()
    )

    ps = _patches(
        entity_svc,
        jurisdiction_svc,
        project_svc,
        group_svc,
        status_svc,
        elms_data=elms_data,
        group_config=single_project_config,
        elms_projects=[_VOTE_PROJECT_DEF],
    )
    for p in ps:
        p.start()
    try:
        await import_scorecard_projects()
    finally:
        for p in reversed(ps):
            p.stop()

    calls = status_mock.create_status_record.call_args_list
    assert len(calls) == 2
    for call in calls:
        assert call.args[0].status == EntityStatus.UNKNOWN


@pytest.mark.asyncio
async def test_sponsorship_project_defaults_unmatched_entities_to_neutral() -> None:
    """Entities absent from the sponsorship cache are assigned NEUTRAL (not a cosponsor)
    when no paired vote data exists (IL-style) or when they ARE in the vote roll call."""
    from scripts.import_scorecard_projects import import_scorecard_projects

    # IL sponsorship: no vote data at all, cache is empty → all get NEUTRAL
    il_data: dict[str, dict] = {"il-test-sponsorship": {}}

    entity_svc, jurisdiction_svc, project_svc, group_svc, status_svc, status_mock, _ = (
        _make_services(jurisdiction_name="Illinois State Senate")
    )

    ps = _patches(
        entity_svc,
        jurisdiction_svc,
        project_svc,
        group_svc,
        status_svc,
        il_data=il_data,
        group_config=_TEST_GROUP_CONFIG_IL,
        il_projects=[_IL_SPONSOR_PROJECT_DEF],
    )
    for p in ps:
        p.start()
    try:
        await import_scorecard_projects()
    finally:
        for p in reversed(ps):
            p.stop()

    calls = status_mock.create_status_record.call_args_list
    assert len(calls) == 2
    for call in calls:
        assert call.args[0].status == EntityStatus.NEUTRAL


@pytest.mark.asyncio
async def test_elms_sponsorship_uses_vote_to_detect_not_in_office() -> None:
    """Entity absent from the paired vote roll call is assigned UNKNOWN on the sponsorship project,
    even if they would otherwise default to NEUTRAL."""
    from scripts.import_scorecard_projects import import_scorecard_projects

    # Entity A (alice johnson) was in vote roll call; Entity B (bob smith) was not
    # Neither is in the sponsorship cache
    elms_data = {
        "test-vote": {
            "alice johnson": "solid_approval",
            # bob smith absent from vote → was not in office
        },
        "test-sponsorship": {
            # no cosponsors
        },
    }

    entity_svc, jurisdiction_svc, project_svc, group_svc, status_svc, status_mock, _ = (
        _make_services()
    )

    ps = _patches(
        entity_svc,
        jurisdiction_svc,
        project_svc,
        group_svc,
        status_svc,
        elms_data=elms_data,
    )
    for p in ps:
        p.start()
    try:
        await import_scorecard_projects()
    finally:
        for p in reversed(ps):
            p.stop()

    all_calls = status_mock.create_status_record.call_args_list
    assert len(all_calls) == 4  # 2 entities × 2 projects

    # Find calls for entity B (bob smith) — should be UNKNOWN on sponsorship project
    # The sponsorship project is the second created; but we can match by entity_id
    entity_b_calls = [c for c in all_calls if c.args[0].entity_id == _ENTITY_B_ID]
    assert len(entity_b_calls) == 2  # one per project

    # Entity B was absent from vote → UNKNOWN on sponsorship project
    entity_b_statuses = {c.args[0].status for c in entity_b_calls}
    assert EntityStatus.UNKNOWN in entity_b_statuses


@pytest.mark.asyncio
async def test_elms_cosponsor_in_vote_gets_solid_approval_on_sponsorship() -> None:
    """Entity who is both in the vote roll call AND in the sponsorship cache gets SOLID_APPROVAL."""
    from scripts.import_scorecard_projects import import_scorecard_projects

    # Entity A (alice johnson) voted AND is a cosponsor
    # Entity B (bob smith) was absent from vote → UNKNOWN
    elms_data = {
        "test-vote": {
            "alice johnson": "solid_approval",
        },
        "test-sponsorship": {
            "alice johnson": "solid_approval",  # alice is a cosponsor
        },
    }

    entity_svc, jurisdiction_svc, project_svc, group_svc, status_svc, status_mock, _ = (
        _make_services()
    )

    ps = _patches(
        entity_svc,
        jurisdiction_svc,
        project_svc,
        group_svc,
        status_svc,
        elms_data=elms_data,
    )
    for p in ps:
        p.start()
    try:
        await import_scorecard_projects()
    finally:
        for p in reversed(ps):
            p.stop()

    all_calls = status_mock.create_status_record.call_args_list
    assert len(all_calls) == 4  # 2 entities × 2 projects

    # Entity A on sponsorship project should be SOLID_APPROVAL (in cache + in vote)
    entity_a_calls = [c for c in all_calls if c.args[0].entity_id == _ENTITY_A_ID]
    entity_a_statuses = {c.args[0].status for c in entity_a_calls}
    assert EntityStatus.SOLID_APPROVAL in entity_a_statuses

    # Entity B absent from vote → UNKNOWN for sponsorship
    entity_b_calls = [c for c in all_calls if c.args[0].entity_id == _ENTITY_B_ID]
    entity_b_statuses = {c.args[0].status for c in entity_b_calls}
    assert EntityStatus.UNKNOWN in entity_b_statuses


@pytest.mark.asyncio
async def test_creates_status_records_for_all_entities() -> None:
    """One EntityStatusRecord is created for every entity × project combination."""
    from scripts.import_scorecard_projects import import_scorecard_projects

    # 3 entities, 2 projects → 6 status records
    three_entities = [
        make_entity(id=uuid4(), name="Alice Johnson", jurisdiction_id=_JURISDICTION_ID),
        make_entity(id=uuid4(), name="Bob Smith", jurisdiction_id=_JURISDICTION_ID),
        make_entity(
            id=uuid4(), name="Carol Williams", jurisdiction_id=_JURISDICTION_ID
        ),
    ]

    entity_svc, jurisdiction_svc, project_svc, group_svc, status_svc, status_mock, _ = (
        _make_services(entities=three_entities)
    )

    ps = _patches(entity_svc, jurisdiction_svc, project_svc, group_svc, status_svc)
    for p in ps:
        p.start()
    try:
        await import_scorecard_projects()
    finally:
        for p in reversed(ps):
            p.stop()

    assert status_mock.create_status_record.call_count == 6  # 3 entities × 2 projects
