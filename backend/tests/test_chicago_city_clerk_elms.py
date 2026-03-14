"""Unit tests for the ELMS API client (app.imports.sources.chicago_city_clerk_elms.py)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.imports.sources.chicago_city_clerk_elms import (
    ELMSClient,
    normalize_name,
    vote_value_to_entity_status,
)
from app.models.pydantic.models import EntityStatus


# ---------------------------------------------------------------------------
# normalize_name — pure function tests
# ---------------------------------------------------------------------------


class TestNormalizeName:
    def test_comma_reversed_name(self):
        # ELMS "Last, First M." → reversed + middle initial stripped → "first last"
        assert normalize_name("Lawson, Bennett R.") == "bennett lawson"

    def test_comma_reversed_hyphenated(self):
        assert normalize_name("Ramirez-Rosa, Carlos G.") == "carlos ramirezrosa"

    def test_comma_reversed_multi_part_last(self):
        assert normalize_name("La Spata, Daniel") == "daniel la spata"

    def test_strips_middle_initial(self):
        assert normalize_name("Nicole T. Lee") == "nicole lee"

    def test_removes_ald_title_prefix(self):
        assert normalize_name("Ald. Maria Hadden") == "maria hadden"

    def test_removes_alderperson_prefix(self):
        assert normalize_name("Alderperson Carlos Ramirez-Rosa") == "carlos ramirezrosa"

    def test_lowercases_and_strips(self):
        assert normalize_name("WALTER BURNETT") == "walter burnett"

    def test_collapses_whitespace(self):
        assert normalize_name("  Carlos   Ramirez-Rosa  ") == "carlos ramirezrosa"

    def test_removes_punctuation_but_keeps_spaces(self):
        # "Jr." becomes "jr" (2 chars, kept); comma is handled before punct strip
        assert normalize_name("BURNETT JR., WALTER") == "walter burnett jr"

    def test_handles_jr_suffix(self):
        assert normalize_name("Walter Burnett Jr.") == "walter burnett jr"

    def test_plain_name_unchanged_except_case(self):
        assert normalize_name("Maria Hadden") == "maria hadden"

    def test_alderwoman_prefix_removed(self):
        assert normalize_name("Alderwoman Michele Smith") == "michele smith"

    def test_elms_name_matches_db_name(self):
        """ELMS 'Last, First M.' normalizes to the same value as a plain DB name."""
        elms_name = normalize_name("Lee, Nicole T.")
        db_name = normalize_name("Nicole Lee")
        assert elms_name == db_name

    def test_elms_hyphen_matches_db_name(self):
        elms_name = normalize_name("Ramirez-Rosa, Carlos G.")
        db_name = normalize_name("Carlos Ramirez-Rosa")
        assert elms_name == db_name


# ---------------------------------------------------------------------------
# vote_value_to_entity_status — pure function tests
# ---------------------------------------------------------------------------


class TestVoteValueToEntityStatus:
    def test_yea_maps_to_solid_approval(self):
        assert vote_value_to_entity_status("Yea") == EntityStatus.SOLID_APPROVAL

    def test_nay_maps_to_solid_disapproval(self):
        assert vote_value_to_entity_status("Nay") == EntityStatus.SOLID_DISAPPROVAL

    def test_abstain_maps_to_neutral(self):
        assert vote_value_to_entity_status("Abstain") == EntityStatus.NEUTRAL

    def test_recuse_maps_to_neutral(self):
        assert vote_value_to_entity_status("Recuse") == EntityStatus.NEUTRAL

    def test_absent_maps_to_unknown(self):
        assert vote_value_to_entity_status("Absent") == EntityStatus.UNKNOWN

    def test_not_voting_maps_to_unknown(self):
        assert vote_value_to_entity_status("Not Voting") == EntityStatus.UNKNOWN

    def test_unknown_value_maps_to_unknown(self):
        assert vote_value_to_entity_status("MYSTERY_VALUE") == EntityStatus.UNKNOWN

    def test_case_insensitive_yea(self):
        assert vote_value_to_entity_status("YEA") == EntityStatus.SOLID_APPROVAL

    def test_case_insensitive_nay(self):
        assert vote_value_to_entity_status("NAY") == EntityStatus.SOLID_DISAPPROVAL


# ---------------------------------------------------------------------------
# ELMSClient.get_matter — mocked HTTP
# ---------------------------------------------------------------------------


def _make_response_ctx(json_data: object, status: int = 200) -> tuple:
    """Build a mock aiohttp response async context manager."""
    mock_response = AsyncMock()
    mock_response.status = status
    # Use side_effect so the mock accepts keyword args (e.g. content_type=None)
    mock_response.json = AsyncMock(side_effect=lambda **_kwargs: json_data)
    mock_response.raise_for_status = MagicMock()
    if status >= 400 and status != 404:
        import aiohttp

        mock_response.raise_for_status.side_effect = aiohttp.ClientResponseError(
            request_info=MagicMock(), history=(), status=status
        )
    ctx = AsyncMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_response)
    ctx.__aexit__ = AsyncMock(return_value=False)
    return ctx, mock_response


def _make_session_ctx(response_ctx) -> AsyncMock:
    session_mock = AsyncMock()
    session_mock.get = MagicMock(return_value=response_ctx)
    session_ctx = AsyncMock()
    session_ctx.__aenter__ = AsyncMock(return_value=session_mock)
    session_ctx.__aexit__ = AsyncMock(return_value=False)
    return session_ctx


_SAMPLE_MATTER = {
    "matterId": "54028B60-C4FC-EE11-A1FE-001DD804AF4C",
    "sponsors": [
        {
            "sponsorName": "Lawson, Bennett R.",
            "sponsorType": "Sponsor",
            "personId": "aaa",
        },
        {
            "sponsorName": "La Spata, Daniel",
            "sponsorType": "CoSponsor",
            "personId": "bbb",
        },
    ],
    "actions": [
        {
            "actionName": "Referred",
            "actionByName": "City Council",
            "votes": [],
        },
        {
            "actionName": "Recommended to Pass",
            "actionByName": "Committee on Zoning",
            "votes": [
                {"voterName": "Smith, Jane A.", "vote": "Yea", "personId": "ccc"},
            ],
        },
        {
            "actionName": "Passed",
            "actionByName": "City Council",
            "votes": [
                {"voterName": "Smith, Jane A.", "vote": "Yea", "personId": "ccc"},
                {"voterName": "Jones, Bob", "vote": "Nay", "personId": "ddd"},
            ],
        },
    ],
}


class TestGetMatter:
    @pytest.mark.asyncio
    async def test_returns_matter_when_found(self):
        response_ctx, _ = _make_response_ctx(_SAMPLE_MATTER)
        session_ctx = _make_session_ctx(response_ctx)

        with patch(
            "app.imports.sources.chicago_city_clerk_elms.aiohttp.ClientSession",
            return_value=session_ctx,
        ):
            client = ELMSClient()
            result = await client.get_matter("54028B60-C4FC-EE11-A1FE-001DD804AF4C")

        assert result is not None
        assert result["matterId"] == "54028B60-C4FC-EE11-A1FE-001DD804AF4C"

    @pytest.mark.asyncio
    async def test_returns_none_on_404(self):
        response_ctx, _ = _make_response_ctx({}, status=404)
        session_ctx = _make_session_ctx(response_ctx)

        with patch(
            "app.imports.sources.chicago_city_clerk_elms.aiohttp.ClientSession",
            return_value=session_ctx,
        ):
            client = ELMSClient()
            result = await client.get_matter("nonexistent-guid")

        assert result is None

    @pytest.mark.asyncio
    async def test_raises_on_server_error(self):
        import aiohttp

        response_ctx, _ = _make_response_ctx({}, status=500)
        session_ctx = _make_session_ctx(response_ctx)

        with patch(
            "app.imports.sources.chicago_city_clerk_elms.aiohttp.ClientSession",
            return_value=session_ctx,
        ):
            client = ELMSClient()
            with pytest.raises(aiohttp.ClientResponseError):
                await client.get_matter("some-guid")

    @pytest.mark.asyncio
    async def test_calls_correct_url(self):
        response_ctx, _ = _make_response_ctx(_SAMPLE_MATTER)
        session_mock = AsyncMock()
        session_mock.get = MagicMock(return_value=response_ctx)
        session_ctx = AsyncMock()
        session_ctx.__aenter__ = AsyncMock(return_value=session_mock)
        session_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "app.imports.sources.chicago_city_clerk_elms.aiohttp.ClientSession",
            return_value=session_ctx,
        ):
            client = ELMSClient(base_url="https://test.example.com")
            await client.get_matter("MY-GUID")

        session_mock.get.assert_called_once_with(
            "https://test.example.com/matter/MY-GUID"
        )

    @pytest.mark.asyncio
    async def test_json_called_with_content_type_none(self):
        """get_matter passes content_type=None to bypass the ELMS API's text/plain header."""
        response_ctx, mock_response = _make_response_ctx(_SAMPLE_MATTER)
        session_ctx = _make_session_ctx(response_ctx)

        with patch(
            "app.imports.sources.chicago_city_clerk_elms.aiohttp.ClientSession",
            return_value=session_ctx,
        ):
            client = ELMSClient()
            await client.get_matter("some-guid")

        mock_response.json.assert_called_once_with(content_type=None)


# ---------------------------------------------------------------------------
# ELMSClient.extract_votes — synchronous, no HTTP
# ---------------------------------------------------------------------------


class TestExtractVotes:
    def test_prefers_city_council_vote_over_committee(self):
        """When both a committee vote and a council vote exist, returns the council one."""
        client = ELMSClient()
        result = client.extract_votes(_SAMPLE_MATTER)

        assert result is not None
        # The "Passed / City Council" action has 2 votes
        assert len(result) == 2
        assert result[0]["voterName"] == "Smith, Jane A."

    def test_returns_none_when_no_votes(self):
        matter = {
            **_SAMPLE_MATTER,
            "actions": [
                {"actionName": "Referred", "actionByName": "City Council", "votes": []}
            ],
        }
        client = ELMSClient()
        assert client.extract_votes(matter) is None

    def test_falls_back_to_committee_vote_if_no_council_vote(self):
        """If no City Council vote, falls back to any action with votes."""
        matter = {
            **_SAMPLE_MATTER,
            "actions": [
                {
                    "actionName": "Passed",
                    "actionByName": "Some Committee",
                    "votes": [{"voterName": "A", "vote": "Yea", "personId": "x"}],
                }
            ],
        }
        client = ELMSClient()
        result = client.extract_votes(matter)
        assert result is not None
        assert len(result) == 1

    def test_takes_last_council_vote_when_multiple(self):
        """When multiple council roll-calls exist, takes the last (final passage)."""
        matter = {
            **_SAMPLE_MATTER,
            "actions": [
                {
                    "actionName": "Failed",
                    "actionByName": "City Council",
                    "votes": [{"voterName": "A", "vote": "Nay", "personId": "x"}],
                },
                {
                    "actionName": "Passed",
                    "actionByName": "City Council",
                    "votes": [{"voterName": "A", "vote": "Yea", "personId": "x"}],
                },
            ],
        }
        client = ELMSClient()
        result = client.extract_votes(matter)
        assert result is not None
        assert result[0]["vote"] == "Yea"

    def test_returns_none_for_missing_actions_key(self):
        client = ELMSClient()
        assert client.extract_votes({"matterId": "x"}) is None

    def test_returns_none_for_null_actions(self):
        client = ELMSClient()
        assert client.extract_votes({"matterId": "x", "actions": None}) is None


# ---------------------------------------------------------------------------
# ELMSClient.extract_sponsors — synchronous, no HTTP
# ---------------------------------------------------------------------------


class TestExtractSponsors:
    def test_returns_all_sponsors(self):
        client = ELMSClient()
        result = client.extract_sponsors(_SAMPLE_MATTER)
        assert len(result) == 2

    def test_returns_correct_fields(self):
        client = ELMSClient()
        result = client.extract_sponsors(_SAMPLE_MATTER)
        assert result[0]["sponsorName"] == "Lawson, Bennett R."
        assert result[0]["sponsorType"] == "Sponsor"
        assert result[1]["sponsorType"] == "CoSponsor"

    def test_returns_empty_list_when_no_sponsors(self):
        client = ELMSClient()
        assert client.extract_sponsors({"matterId": "x", "sponsors": []}) == []

    def test_returns_empty_list_when_sponsors_key_missing(self):
        client = ELMSClient()
        assert client.extract_sponsors({"matterId": "x"}) == []

    def test_returns_empty_list_when_sponsors_null(self):
        client = ELMSClient()
        assert client.extract_sponsors({"matterId": "x", "sponsors": None}) == []
