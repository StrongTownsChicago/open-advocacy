from typing import Any
import aiohttp
import logging
from abc import abstractmethod

from app.imports.base import DataSource

logger = logging.getLogger(__name__)


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
