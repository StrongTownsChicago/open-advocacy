"""Unit tests for OpenStateBillsClient extraction methods and OPENSTATES_VOTE_TO_STATUS."""

from app.imports.sources.openstates import (
    OPENSTATES_VOTE_TO_STATUS,
    OpenStateBillsClient,
    openstates_vote_option_to_status,
)
from app.models.pydantic.models import EntityStatus

# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

MOCK_BILL_WITH_SPONSORSHIPS: dict = {
    "id": "ocd-bill/test-1",
    "identifier": "SB 4061",
    "sponsorships": [
        {
            "name": "Don Harmon",
            "entity_type": "person",
            "classification": "primary",
            "primary": True,
            "person": {"id": "p1", "name": "Don Harmon"},
        },
        {
            "name": "Anna Moeller",
            "entity_type": "person",
            "classification": "cosponsor",
            "primary": False,
            "person": {"id": "p2", "name": "Anna Moeller"},
        },
    ],
}

MOCK_BILL_WITH_VOTES: dict = {
    "id": "ocd-bill/test-2",
    "identifier": "SB 2222",
    "votes": [
        {
            "organization": {"classification": "upper"},
            "result": "pass",
            "date": "2025-05-20",
            "votes": [
                {"option": "yes", "voter": {"name": "Don Harmon"}},
                {"option": "no", "voter": {"name": "John Smith"}},
            ],
        }
    ],
}

MOCK_BILL_WITH_COMMITTEE_AND_CHAMBER_VOTES: dict = {
    "id": "ocd-bill/test-3",
    "identifier": "SB 3333",
    "votes": [
        {
            "organization": {"classification": "committee"},
            "result": "pass",
            "date": "2025-03-01",
            "votes": [
                {"option": "yes", "voter": {"name": "Committee Member"}},
            ],
        },
        {
            "organization": {"classification": "upper"},
            "result": "pass",
            "date": "2025-05-20",
            "votes": [
                {"option": "yes", "voter": {"name": "Don Harmon"}},
            ],
        },
    ],
}

MOCK_BILL_EMPTY: dict = {
    "id": "ocd-bill/test-4",
    "identifier": "SB 9999",
    "sponsorships": [],
    "votes": [],
}


# ---------------------------------------------------------------------------
# extract_sponsors
# ---------------------------------------------------------------------------


class TestExtractSponsors:
    def setup_method(self):
        self.client = OpenStateBillsClient(api_key="test-key")

    def test_returns_all_entries(self):
        result = self.client.extract_sponsors(MOCK_BILL_WITH_SPONSORSHIPS)
        assert len(result) == 2

    def test_returns_correct_classifications(self):
        result = self.client.extract_sponsors(MOCK_BILL_WITH_SPONSORSHIPS)
        assert result[0]["classification"] == "primary"
        assert result[1]["classification"] == "cosponsor"

    def test_empty_sponsorships_returns_empty_list(self):
        result = self.client.extract_sponsors(MOCK_BILL_EMPTY)
        assert result == []

    def test_missing_sponsorships_key_returns_empty_list(self):
        result = self.client.extract_sponsors({"id": "x"})
        assert result == []

    def test_null_sponsorships_returns_empty_list(self):
        result = self.client.extract_sponsors({"id": "x", "sponsorships": None})
        assert result == []


# ---------------------------------------------------------------------------
# extract_votes
# ---------------------------------------------------------------------------


class TestExtractVotes:
    def setup_method(self):
        self.client = OpenStateBillsClient(api_key="test-key")

    def test_returns_votes_from_single_chamber_vote(self):
        result = self.client.extract_votes(MOCK_BILL_WITH_VOTES)
        assert result is not None
        assert len(result) == 2
        assert result[0]["option"] == "yes"

    def test_prefers_chamber_vote_over_committee_vote(self):
        result = self.client.extract_votes(MOCK_BILL_WITH_COMMITTEE_AND_CHAMBER_VOTES)
        assert result is not None
        assert len(result) == 1
        assert result[0]["voter"]["name"] == "Don Harmon"

    def test_empty_votes_returns_none(self):
        result = self.client.extract_votes(MOCK_BILL_EMPTY)
        assert result is None

    def test_missing_votes_key_returns_none(self):
        result = self.client.extract_votes({"id": "x"})
        assert result is None

    def test_null_votes_returns_none(self):
        result = self.client.extract_votes({"id": "x", "votes": None})
        assert result is None

    def test_returns_most_recent_when_multiple_chamber_votes(self):
        bill = {
            "id": "ocd-bill/test-multi",
            "votes": [
                {
                    "organization": {"classification": "upper"},
                    "date": "2025-01-01",
                    "votes": [{"option": "no", "voter": {"name": "Alice"}}],
                },
                {
                    "organization": {"classification": "upper"},
                    "date": "2025-06-01",
                    "votes": [{"option": "yes", "voter": {"name": "Alice"}}],
                },
            ],
        }
        result = self.client.extract_votes(bill)
        assert result is not None
        assert result[0]["option"] == "yes"


# ---------------------------------------------------------------------------
# OPENSTATES_VOTE_TO_STATUS mapping
# ---------------------------------------------------------------------------


class TestOpenStatesVoteToStatus:
    def test_yes_maps_to_solid_approval(self):
        assert OPENSTATES_VOTE_TO_STATUS["yes"] == EntityStatus.SOLID_APPROVAL

    def test_no_maps_to_solid_disapproval(self):
        assert OPENSTATES_VOTE_TO_STATUS["no"] == EntityStatus.SOLID_DISAPPROVAL

    def test_abstain_maps_to_neutral(self):
        assert OPENSTATES_VOTE_TO_STATUS["abstain"] == EntityStatus.NEUTRAL

    def test_not_voting_maps_to_neutral(self):
        assert OPENSTATES_VOTE_TO_STATUS["not voting"] == EntityStatus.NEUTRAL

    def test_excused_maps_to_neutral(self):
        assert OPENSTATES_VOTE_TO_STATUS["excused"] == EntityStatus.NEUTRAL

    def test_absent_maps_to_neutral(self):
        assert OPENSTATES_VOTE_TO_STATUS["absent"] == EntityStatus.NEUTRAL


class TestOpenStatesVoteOptionToStatus:
    def test_yes_via_helper(self):
        assert openstates_vote_option_to_status("yes") == EntityStatus.SOLID_APPROVAL

    def test_no_via_helper(self):
        assert openstates_vote_option_to_status("no") == EntityStatus.SOLID_DISAPPROVAL

    def test_unknown_value_returns_unknown(self):
        assert openstates_vote_option_to_status("mystery") == EntityStatus.UNKNOWN

    def test_case_insensitive(self):
        assert openstates_vote_option_to_status("YES") == EntityStatus.SOLID_APPROVAL
