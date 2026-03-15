import re
from typing import Any
import aiohttp
import logging
from abc import abstractmethod

from app.imports.base import DataSource
from app.models.pydantic.models import EntityStatus

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# IL name normalization
# ---------------------------------------------------------------------------

_IL_HONORIFIC_PREFIXES = re.compile(
    r"^(representative|rep\.?|senator|sen\.?)\s+", re.IGNORECASE
)
_GENERATIONAL_SUFFIXES = frozenset({"jr", "sr", "ii", "iii", "iv"})


def normalize_il_name(name: str) -> str:
    """Normalize an Illinois legislator name for matching.

    Names from the OpenStates /people endpoint are already in "First Last" order
    (no comma-reversal needed). This function:
    - Strips honorific prefixes (Rep., Representative, Sen., Senator)
    - Removes punctuation
    - Strips single-character tokens (middle initials)
    - Strips generational suffixes (Jr, Sr, II, III, IV)
    - Lowercases and collapses whitespace
    """
    # Strip honorific prefix before punctuation removal so "Rep." → "rep " works
    name = _IL_HONORIFIC_PREFIXES.sub("", name.strip())
    # Remove all punctuation (apostrophes, periods, hyphens, etc.)
    name = re.sub(r"[^\w\s]", "", name)
    # Lowercase
    name = name.lower()
    # Collapse whitespace
    tokens = name.split()
    # Remove single-character tokens (middle initials) and generational suffixes
    tokens = [t for t in tokens if len(t) > 1 and t not in _GENERATIONAL_SUFFIXES]
    return " ".join(tokens)


# ---------------------------------------------------------------------------
# OpenStates vote-to-EntityStatus mapping
# ---------------------------------------------------------------------------

OPENSTATES_VOTE_TO_STATUS: dict[str, EntityStatus] = {
    "yes": EntityStatus.SOLID_APPROVAL,
    "no": EntityStatus.SOLID_DISAPPROVAL,
    "abstain": EntityStatus.NEUTRAL,
    "not voting": EntityStatus.NEUTRAL,
    "excused": EntityStatus.NEUTRAL,
    "absent": EntityStatus.NEUTRAL,
}


def openstates_vote_option_to_status(option: str) -> EntityStatus:
    """Convert an OpenStates vote option string to an EntityStatus.

    Falls back to UNKNOWN for unrecognized values.
    """
    return OPENSTATES_VOTE_TO_STATUS.get(option.lower(), EntityStatus.UNKNOWN)


# ---------------------------------------------------------------------------
# OpenStates bills client
# ---------------------------------------------------------------------------

IL_JURISDICTION_ID = "ocd-jurisdiction/country:us/state:il/government"


class OpenStateBillsClient:
    """Client for fetching bill data from the OpenStates v3 API."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://v3.openstates.org",
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.bills_endpoint = f"{base_url}/bills"

    async def get_bill(
        self,
        session: str,
        bill_identifier: str,
        jurisdiction_id: str,
        include: str,
    ) -> dict[str, Any] | None:
        """Fetch a single bill from OpenStates.

        Args:
            session: OpenStates session name, e.g. "104th"
            bill_identifier: Bill identifier, e.g. "SB 4061"
            jurisdiction_id: OCD jurisdiction ID
            include: Field to include, e.g. "sponsorships" or "votes"

        Returns:
            The first matching bill dict, or None if not found.
        """
        headers = {"X-API-Key": self.api_key}
        params: dict[str, Any] = {
            "jurisdiction": jurisdiction_id,
            "identifier": bill_identifier,
            "session": session,
            "include": include,
        }
        async with aiohttp.ClientSession() as http_session:
            async with http_session.get(
                self.bills_endpoint, headers=headers, params=params
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.warning(
                        "OpenStates bills API returned %d for %s: %s",
                        response.status,
                        bill_identifier,
                        error_text,
                    )
                    return None
                data = await response.json()
                results = data.get("results", [])
                if not results:
                    logger.warning("No results found for bill %s", bill_identifier)
                    return None
                return results[0]  # type: ignore[no-any-return]

    def extract_sponsors(self, bill: dict[str, Any]) -> list[dict[str, Any]]:
        """Return the sponsorships list from a bill dict.

        Each entry contains at minimum a ``person`` sub-dict with a ``name``
        field (the canonical OpenStates name) and a ``classification`` field
        (``"primary"`` or ``"cosponsor"``).
        """
        return list(bill.get("sponsorships") or [])

    def extract_votes(
        self,
        bill: dict[str, Any],
        preferred_classification: str | None = None,
        vote_date: str | None = None,
    ) -> list[dict[str, Any]] | None:
        """Return the vote list from the most relevant vote event.

        Prefers chamber-level votes (``organization.classification`` in
        ``{"upper", "lower"}``) over committee votes.  If ``preferred_classification``
        is given (``"upper"`` or ``"lower"``), picks votes from that chamber first —
        useful for bills like SB 2111 that have both Senate and House floor votes.

        If ``vote_date`` is given (``"YYYY-MM-DD"``), restricts to vote events that
        started on that date — use this to pin to a specific floor vote (e.g. the
        Third Reading rather than a later concurrence vote).

        The OpenStates API returns vote events newest-first, so ``[0]`` is the most
        recent.  Falls back to any chamber vote, then any vote event.
        Returns ``None`` if the bill has no matching vote events.
        """
        vote_events: list[dict[str, Any]] = list(bill.get("votes") or [])
        if not vote_events:
            return None

        chamber_votes = [
            v
            for v in vote_events
            if v.get("organization", {}).get("classification") in ("upper", "lower")
        ]

        if preferred_classification and chamber_votes:
            preferred = [
                v
                for v in chamber_votes
                if v.get("organization", {}).get("classification")
                == preferred_classification
            ]
            if vote_date:
                preferred = [v for v in preferred if v.get("start_date") == vote_date]
            if preferred:
                return preferred[0].get("votes") or None

        if vote_date:
            chamber_votes = [
                v for v in chamber_votes if v.get("start_date") == vote_date
            ]
        candidates = chamber_votes if chamber_votes else vote_events
        chosen_event = max(
            candidates, key=lambda v: v.get("date") or v.get("start_date") or ""
        )
        return chosen_event.get("votes") or None


class OpenStatesDataSource(DataSource[dict[str, list[dict[str, Any]]]]):
    """Base data source for OpenStates API data."""

    def __init__(
        self,
        api_key: str,
        state_code: str,
        base_url: str = "https://v3.openstates.org",
        include_fields: list[str] | None = None,
    ):
        self.api_key = api_key
        self.state_code = state_code.lower()
        self.base_url = base_url
        self.people_endpoint = f"{base_url}/people"
        self.geo_endpoint = f"{base_url}/people.geo"

        # Cache for fetched data
        self._cached_data: dict[str, list[dict[str, Any]]] | None = None

        # Default included fields
        self.include_fields = include_fields or [
            "other_names",
            "other_identifiers",
            "links",
            "sources",
            "offices",
        ]

    @property
    @abstractmethod
    def jurisdiction_id(self) -> str:
        """OCD jurisdiction ID for the state."""
        pass

    async def fetch_data(self) -> dict[str, list[dict[str, Any]]]:
        """
        Fetch legislator data from the OpenStates API.

        Returns:
            Dict with 'house' and 'senate' lists of legislator data
        """
        # Return cached data if available
        if self._cached_data is not None:
            logger.info(f"Using cached {self.state_code.upper()} legislators data")
            return self._cached_data

        logger.info(
            f"Fetching {self.state_code.upper()} legislators from OpenStates API..."
        )

        legislators: dict[str, list[dict[str, Any]]] = {"house": [], "senate": []}

        headers = {
            "X-API-Key": self.api_key,
        }

        try:
            async with aiohttp.ClientSession() as session:
                # Fetch legislators
                # We'll need to paginate to get all results
                url = self.people_endpoint

                params: dict[str, Any] = {
                    "jurisdiction": self.jurisdiction_id,
                    "include": self.include_fields,
                    "per_page": 50,
                }

                page = 1
                total_fetched = 0

                while True:
                    params["page"] = page
                    async with session.get(
                        url, headers=headers, params=params
                    ) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            logger.error(
                                f"API request failed: {response.status} - {error_text}"
                            )
                            break

                        data = await response.json()
                        results = data.get("results", [])

                        if not results:
                            break

                        # Sort legislators into house and senate
                        for legislator in results:
                            current_role = legislator.get("current_role", {})
                            if current_role.get("org_classification") == "lower":
                                legislators["house"].append(legislator)
                            elif current_role.get("org_classification") == "upper":
                                legislators["senate"].append(legislator)

                        total_fetched += len(results)
                        logger.info(f"Fetched {len(results)} legislators (page {page})")

                        # Check pagination
                        pagination = data.get("pagination", {})
                        if page >= pagination.get("max_page", 1):
                            break

                        page += 1

                logger.info(
                    f"Fetched {len(legislators['house'])} House representatives and "
                    f"{len(legislators['senate'])} Senators"
                )
                logger.info(f"Total fetched: {total_fetched}")

                # Cache the data
                self._cached_data = legislators
                return legislators
        except Exception as e:
            logger.error(f"Error fetching legislators: {str(e)}")
            return legislators

    async def fetch_by_location(
        self, latitude: float, longitude: float
    ) -> list[dict[str, Any]]:
        """
        Fetch legislators for a specific location using OpenStates API.

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate

        Returns:
            List of legislator data
        """
        logger.info(f"Fetching legislators for location: {latitude}, {longitude}")

        headers = {
            "X-API-Key": self.api_key,
        }

        legislators = []

        try:
            async with aiohttp.ClientSession() as session:
                # Use the people.geo endpoint
                url = self.geo_endpoint

                params: dict[str, Any] = {
                    "lat": latitude,
                    "lng": longitude,
                    "include": self.include_fields,
                }

                async with session.get(url, headers=headers, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(
                            f"API request failed: {response.status} - {error_text}"
                        )
                        return []

                    data = await response.json()
                    legislators = data.get("results", [])

                    logger.info(f"Fetched {len(legislators)} legislators for location")
                    return legislators
        except Exception as e:
            logger.error(f"Error fetching legislators by location: {str(e)}")
            return []

    def get_source_info(self) -> dict[str, Any]:
        """Get information about the data source."""
        return {
            "name": f"{self.state_code.upper()} Legislators Data",
            "url": self.base_url,
            "type": "OpenStates API",
            "description": f"OpenStates data on {self.state_code.upper()} state legislators",
        }


class IllinoisLegislatorsDataSource(OpenStatesDataSource):
    """Data source for Illinois legislators."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://v3.openstates.org",
        include_fields: list[str] | None = None,
    ):
        super().__init__(
            api_key=api_key,
            state_code="il",
            base_url=base_url,
            include_fields=include_fields,
        )

    @property
    def jurisdiction_id(self) -> str:
        return "ocd-jurisdiction/country:us/state:il/government"
