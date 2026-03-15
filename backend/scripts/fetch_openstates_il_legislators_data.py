"""Fetch IL legislators from OpenStates and write them to app/data/il_legislators_data.py.

Fetches the full profile for every current Illinois House representative and
State Senator so that the illinois location import works without network access
(and without burning the 250 req/day OpenStates quota on every cold-start).

Run this script whenever you want to refresh the cached legislators:

    python -m scripts.fetch_openstates_il_legislators_data

The generated file (app/data/il_legislators_data.py) should be committed to the
repository so that import_data illinois works offline.
"""

import asyncio
import logging
import reprlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiohttp

from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fetch-openstates-il-legislators")

IL_JURISDICTION_ID = "ocd-jurisdiction/country:us/state:il/government"
BASE_URL = "https://v3.openstates.org"
PEOPLE_ENDPOINT = f"{BASE_URL}/people"
INCLUDE_FIELDS = ["other_names", "other_identifiers", "links", "sources", "offices"]
PER_PAGE = 50

OUTPUT_PATH = (
    Path(__file__).resolve().parent.parent / "app" / "data" / "il_legislators_data.py"
)


async def fetch_legislators(api_key: str) -> dict[str, list[dict[str, Any]]]:
    """Fetch all current IL House and Senate members from the OpenStates API."""
    legislators: dict[str, list[dict[str, Any]]] = {"house": [], "senate": []}
    headers = {"X-API-Key": api_key}
    params: dict[str, Any] = {
        "jurisdiction": IL_JURISDICTION_ID,
        "include": INCLUDE_FIELDS,
        "per_page": PER_PAGE,
        "page": 1,
    }

    async with aiohttp.ClientSession() as session:
        page = 1
        while True:
            params["page"] = page
            async with session.get(
                PEOPLE_ENDPOINT, headers=headers, params=params
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(
                        "API request failed: %d - %s", response.status, error_text
                    )
                    break

                data = await response.json()
                results: list[dict[str, Any]] = data.get("results", [])
                if not results:
                    break

                for legislator in results:
                    current_role = legislator.get("current_role") or {}
                    org = current_role.get("org_classification")
                    if org == "lower":
                        legislators["house"].append(legislator)
                    elif org == "upper":
                        legislators["senate"].append(legislator)

                logger.info("Page %d: fetched %d legislators", page, len(results))
                pagination = data.get("pagination", {})
                if page >= pagination.get("max_page", 1):
                    break
                page += 1
                await asyncio.sleep(1)  # be polite

    logger.info(
        "Total: %d House, %d Senate",
        len(legislators["house"]),
        len(legislators["senate"]),
    )
    return legislators


def _repr_str(value: Any) -> str:
    """Return a repr string for a scalar value (str, None, int)."""
    if value is None:
        return "None"
    if isinstance(value, str):
        # Escape backslashes and quotes
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return repr(value)


def _serialize_list(items: list[Any], indent: int) -> str:
    """Serialize a list of dicts/scalars to Python source."""
    pad = " " * indent
    inner_pad = " " * (indent + 4)
    lines = ["["]
    for item in items:
        if isinstance(item, dict):
            lines.append(inner_pad + _serialize_dict(item, indent + 4) + ",")
        else:
            lines.append(inner_pad + _repr_str(item) + ",")
    lines.append(pad + "]")
    return "\n".join(lines)


def _serialize_dict(d: dict[str, Any], indent: int) -> str:
    """Serialize a dict to Python source (inline for small dicts)."""
    pad = " " * indent
    inner_pad = " " * (indent + 4)
    lines = ["{"]
    for key, value in d.items():
        if isinstance(value, dict):
            lines.append(
                inner_pad
                + _repr_str(key)
                + ": "
                + _serialize_dict(value, indent + 4)
                + ","
            )
        elif isinstance(value, list):
            lines.append(
                inner_pad
                + _repr_str(key)
                + ": "
                + _serialize_list(value, indent + 4)
                + ","
            )
        else:
            lines.append(inner_pad + _repr_str(key) + ": " + _repr_str(value) + ",")
    lines.append(pad + "}")
    return "\n".join(lines)


def write_legislators_module(data: dict[str, list[dict[str, Any]]]) -> None:
    """Write the IL legislators data as a Python module."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    lines = [
        "# -*- coding: utf-8 -*-",
        "# Auto-generated by scripts/fetch_openstates_il_legislators_data.py",
        "# Source: OpenStates API",
        f"# Generated: {timestamp}",
        "from typing import Any",
        "",
        "IL_LEGISLATORS_DATA: dict[str, list[dict[str, Any]]] = {",
    ]

    for chamber in ("house", "senate"):
        members = data.get(chamber, [])
        lines.append(f'    "{chamber}": [')
        for member in members:
            serialized = _serialize_dict(member, 8)
            lines.append(f"        {serialized},")
        lines.append("    ],")

    lines.append("}")
    lines.append("")
    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    logger.info(
        "Wrote %d House + %d Senate legislators to %s",
        len(data.get("house", [])),
        len(data.get("senate", [])),
        OUTPUT_PATH,
    )
    _ = reprlib  # suppress unused import


async def main() -> None:
    api_key = settings.OPENSTATES_API_KEY
    if not api_key:
        raise ValueError(
            "OPENSTATES_API_KEY is not set. "
            "Set it in your environment or .env file before running this script."
        )

    data = await fetch_legislators(api_key)

    if not data["house"] and not data["senate"]:
        logger.error("No legislators fetched — output file not written.")
        return

    write_legislators_module(data)


if __name__ == "__main__":
    asyncio.run(main())
