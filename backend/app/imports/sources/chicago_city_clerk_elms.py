"""Chicago ELMS API client for fetching legislative data.

Replaces the frozen Legistar WebAPI (webapi.legistar.com, data cutoff June 2023)
with the new Chicago City Clerk eLMS API (api.chicityclerkelms.chicago.gov),
which is public, unauthenticated, and covers matters from December 2010 to present.

API docs / Swagger UI: https://api.chicityclerkelms.chicago.gov/
"""

import logging
import re
import string
from typing import Any

import aiohttp

from app.models.pydantic.models import EntityStatus

logger = logging.getLogger(__name__)

BASE_URL = "https://api.chicityclerkelms.chicago.gov"

VOTE_VALUE_TO_STATUS: dict[str, EntityStatus] = {
    "yea": EntityStatus.SOLID_APPROVAL,
    "nay": EntityStatus.SOLID_DISAPPROVAL,
    "abstain": EntityStatus.NEUTRAL,
    "recuse": EntityStatus.NEUTRAL,
    "absent": EntityStatus.UNKNOWN,
    "not voting": EntityStatus.UNKNOWN,
}


def normalize_name(name: str) -> str:
    """Normalize a person name for fuzzy matching between ELMS and DB entity names.

    Handles:
    - ELMS comma-reversed format: "Last, First M." → "first last"
    - Middle initials: stripped (single-character tokens removed)
    - Honorific prefixes: Ald., Alderperson, Alderwoman, Alderman
    - Punctuation, extra whitespace, mixed case
    """
    name = name.lower().strip()

    # Handle comma-reversed format ("Last, First M." → "first m last")
    if "," in name:
        parts = name.split(",", 1)
        name = parts[1].strip() + " " + parts[0].strip()

    # Remove punctuation
    name = name.translate(str.maketrans("", "", string.punctuation))

    # Collapse whitespace
    name = re.sub(r"\s+", " ", name).strip()

    # Remove honorific prefixes
    for prefix in ("ald ", "alderperson ", "alderwoman ", "alderman "):
        if name.startswith(prefix):
            name = name[len(prefix):]
            break

    # Strip middle initials (single-character tokens), e.g. "nicole t lee" → "nicole lee"
    tokens = [t for t in name.split() if len(t) > 1]
    return " ".join(tokens)


def vote_value_to_entity_status(vote_value: str) -> EntityStatus:
    """Map an ELMS vote string to an EntityStatus."""
    return VOTE_VALUE_TO_STATUS.get(vote_value.lower(), EntityStatus.UNKNOWN)


class ELMSClient:
    """Async client for the Chicago City Clerk eLMS API.

    Fetches full matter data (sponsors + votes) in a single HTTP call.
    All extraction of sponsors and votes is done synchronously from the
    returned matter dict — no additional HTTP calls are needed.
    """

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url

    async def get_matter(self, matter_id: str) -> dict[str, Any] | None:
        """Fetch a full matter by UUID (the ELMS matterId / ELMS URL param).

        Returns the full matter dict (including sponsors and actions with votes),
        or None if not found (404).
        Raises aiohttp.ClientResponseError on other HTTP errors.
        """
        url = f"{self.base_url}/matter/{matter_id}"
        logger.debug("ELMS get_matter: GET %s", url)
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 404:
                    logger.warning("ELMS matter not found: %s", matter_id)
                    return None
                response.raise_for_status()
                # content_type=None bypasses aiohttp's strict content-type check;
                # the ELMS API returns valid JSON with 'text/plain; charset=utf-8'
                return await response.json(content_type=None)  # type: ignore[return-value]

    def extract_sponsors(self, matter: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract sponsors from a matter dict.

        Returns all entries from matter["sponsors"] regardless of sponsorType
        (Sponsor, CoSponsor, FilingSponsor are all treated as supporting).
        Each entry has keys: sponsorName, sponsorType, personId, office.
        """
        return list(matter.get("sponsors") or [])

    def extract_votes(self, matter: dict[str, Any]) -> list[dict[str, Any]] | None:
        """Extract the council floor vote roll call from a matter dict.

        Searches matter["actions"] for actions with non-empty votes arrays.
        Prefers actions where actionByName contains "Council" (full council
        vote rather than a committee vote). Returns the last matching action's
        votes list, or None if no roll-call vote is found.

        Each vote entry has keys: voterName, vote ("Yea"/"Nay"/"Not Voting"/"Absent"),
        personId.
        """
        actions: list[dict[str, Any]] = matter.get("actions") or []

        # Collect all actions that have a non-empty votes list
        voted_actions = [a for a in actions if a.get("votes")]

        if not voted_actions:
            logger.warning(
                "No roll-call vote found for matter %s", matter.get("matterId")
            )
            return None

        # Prefer a City Council floor vote over a committee vote
        council_actions = [
            a for a in voted_actions
            if "council" in (a.get("actionByName") or "").lower()
        ]
        target_actions = council_actions if council_actions else voted_actions

        # Take the last matching action (chronologically the final passage)
        return list(target_actions[-1]["votes"])
