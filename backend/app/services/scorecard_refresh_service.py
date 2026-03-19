"""Scorecard refresh service: fetch live data and upsert EntityStatusRecords.

This module provides `run_scorecard_refresh()`, which fetches current vote and
sponsorship data from both the Chicago City Clerk eLMS API and the OpenStates
API, then upserts EntityStatusRecord rows for all scorecard projects.

This is the runtime equivalent of running:
    python -m scripts.fetch_elms_scorecard_data   (fetch + write static file)
    python -m scripts.fetch_openstates_il_scorecard_data
    python -m scripts.import_scorecard_projects    (read static file + upsert)

But without the intermediate static file step.
"""

import asyncio
import logging
from typing import Any

import aiohttp

from app.core.config import settings
from app.imports.sources.chicago_city_clerk_elms import (
    ELMSClient,
    normalize_name,
    vote_value_to_entity_status,
)
from app.imports.sources.openstates import (
    IL_JURISDICTION_ID,
    OpenStateBillsClient,
    normalize_il_name,
    openstates_vote_option_to_status,
)
from app.models.pydantic.models import EntityStatus, EntityStatusRecord
from app.services.entity_service import EntityService
from app.services.jurisdiction_service import JurisdictionService
from app.services.project_service import ProjectService
from app.services.status_service import StatusService
from scripts.scorecard_project_data import (
    ALL_IL_SCORECARD_PROJECTS,
    ALL_SCORECARD_PROJECTS,
    GROUP_CONFIG,
    STC_ONLY_IL_SCORECARD_PROJECTS,
)

ALL_IL_PROJECTS_TO_REFRESH = ALL_IL_SCORECARD_PROJECTS + STC_ONLY_IL_SCORECARD_PROJECTS

logger = logging.getLogger(__name__)

MAX_CONCURRENT = 3
IL_SESSION = "104th"


# ---------------------------------------------------------------------------
# ELMS (Chicago) fetch helpers
# ---------------------------------------------------------------------------


async def _fetch_matter(
    session: aiohttp.ClientSession,
    semaphore: asyncio.Semaphore,
    matter_guid: str,
) -> tuple[str, dict[str, Any] | None]:
    """Fetch a single matter from ELMS, returning (guid, matter_dict | None)."""
    client = ELMSClient()
    async with semaphore:
        try:
            url = f"{client.base_url}/matter/{matter_guid}"
            logger.debug("Fetching matter %s", matter_guid)
            async with session.get(url) as response:
                if response.status == 404:
                    logger.warning("Matter not found: %s", matter_guid)
                    return matter_guid, None
                response.raise_for_status()
                data = await response.json(content_type=None)
                logger.info("Fetched matter %s", matter_guid)
                return matter_guid, data
        except Exception:
            logger.exception("Failed to fetch matter %s", matter_guid)
            return matter_guid, None


def _extract_elms_lookup(
    matter: dict[str, Any],
    import_type: str,
    base_slug: str,
) -> dict[str, EntityStatus]:
    """Extract a {normalized_name: EntityStatus} dict from an ELMS matter."""
    client = ELMSClient()
    if import_type == "vote":
        votes = client.extract_votes(matter)
        if votes is None:
            logger.warning("No final passage vote found for %s", base_slug)
            return {}
        return {
            normalize_name(str(v["voterName"])): vote_value_to_entity_status(
                str(v.get("vote", ""))
            )
            for v in votes
            if v.get("voterName")
        }
    else:
        # sponsorship
        sponsors = client.extract_sponsors(matter)
        return {
            normalize_name(str(s["sponsorName"])): EntityStatus.SOLID_APPROVAL
            for s in sponsors
            if s.get("sponsorName")
        }


# ---------------------------------------------------------------------------
# OpenStates (IL) fetch helpers
# ---------------------------------------------------------------------------


async def _fetch_il_bill(
    semaphore: asyncio.Semaphore,
    client: OpenStateBillsClient,
    bill_identifier: str,
    import_type: str,
) -> tuple[str, str, dict[str, Any] | None]:
    """Fetch a single IL bill, returning (bill_identifier, import_type, bill_dict | None)."""
    include = "sponsorships" if import_type == "sponsorship" else "votes"
    async with semaphore:
        try:
            logger.debug("Fetching IL bill %s (%s)", bill_identifier, import_type)
            bill = await client.get_bill(
                session=IL_SESSION,
                bill_identifier=bill_identifier,
                jurisdiction_id=IL_JURISDICTION_ID,
                include=include,
            )
            if bill is not None:
                logger.info("Fetched IL bill %s (%s)", bill_identifier, import_type)
            else:
                logger.warning(
                    "No data returned for IL bill %s (%s)", bill_identifier, import_type
                )
            # Respect OpenStates rate limits: 7 second delay keeps us under 10/min
            await asyncio.sleep(7)
            return bill_identifier, import_type, bill
        except Exception:
            logger.exception(
                "Failed to fetch IL bill %s (%s)", bill_identifier, import_type
            )
            await asyncio.sleep(7)
            return bill_identifier, import_type, None


def _extract_il_lookup(
    bill: dict[str, Any],
    import_type: str,
    base_slug: str,
    chamber: str = "",
    vote_date: str = "",
) -> dict[str, EntityStatus]:
    """Extract a {normalized_name: EntityStatus} dict from an OpenStates bill."""
    client = OpenStateBillsClient(api_key="")  # api_key not needed for extraction
    if import_type == "vote":
        preferred = (
            "upper" if chamber == "senate" else "lower" if chamber == "house" else None
        )
        votes = client.extract_votes(
            bill,
            preferred_classification=preferred,
            vote_date=vote_date or None,
        )
        if votes is None:
            logger.warning("No vote data found for %s", base_slug)
            return {}
        result: dict[str, EntityStatus] = {}
        for v in votes:
            voter = v.get("voter") or {}
            name = voter.get("name") or ""
            if not name:
                continue
            option = str(v.get("option", ""))
            result[normalize_il_name(name)] = openstates_vote_option_to_status(option)
        return result
    else:
        # sponsorship: filter by chamber when specified
        chamber_classification = (
            "upper" if chamber == "senate" else "lower" if chamber == "house" else None
        )
        sponsors = client.extract_sponsors(bill)
        result = {}
        for s in sponsors:
            person = s.get("person") or {}
            name = person.get("name") or ""
            if not name:
                continue
            if chamber_classification:
                current_role = person.get("current_role") or {}
                if current_role.get("org_classification") != chamber_classification:
                    continue
            result[normalize_il_name(name)] = EntityStatus.SOLID_APPROVAL
        return result


# ---------------------------------------------------------------------------
# Main refresh function
# ---------------------------------------------------------------------------


async def run_scorecard_refresh(
    entity_service: EntityService,
    jurisdiction_service: JurisdictionService,
    project_service: ProjectService,
    status_service: StatusService,
) -> dict[str, int]:
    """Fetch live data and upsert EntityStatusRecords for all scorecard projects.

    Fetches from the Chicago City Clerk eLMS API for Chicago projects and from
    the OpenStates API for Illinois state legislature projects.

    Returns a dict with keys:
      - "updated": number of status records successfully upserted
      - "errors": number of failures (missing projects, missing matters, etc.)
    """
    updated = 0
    errors = 0

    elms_lookups, elms_errors = await _fetch_elms_lookups()
    errors += elms_errors

    il_lookups, il_errors = await _fetch_il_lookups()
    errors += il_errors

    # Pre-build ELMS vote lookups for "not in office" detection on paired sponsorship projects
    elms_vote_data_by_guid: dict[str, dict[str, EntityStatus]] = {}
    for project_def in ALL_SCORECARD_PROJECTS:
        if project_def["import_type"] == "vote":
            base_slug = str(project_def["base_slug"])
            elms_vote_data_by_guid[str(project_def["matter_guid"])] = elms_lookups.get(
                base_slug, {}
            )

    for group_cfg in GROUP_CONFIG:
        data_source = str(group_cfg["data_source"])
        slug_prefix = str(group_cfg["slug_prefix"])
        jurisdiction_name = str(group_cfg["jurisdiction_name"])
        base_slugs: set[str] = group_cfg["base_slugs"]  # type: ignore[assignment]

        jurisdiction = await jurisdiction_service.find_by_name(jurisdiction_name)
        if not jurisdiction:
            logger.warning(
                "Jurisdiction '%s' not found; skipping group '%s'.",
                jurisdiction_name,
                group_cfg["name"],
            )
            errors += 1
            continue

        entities = await entity_service.list_entities(jurisdiction_id=jurisdiction.id)
        logger.info(
            "Group '%s': found %d entities in '%s'.",
            group_cfg["name"],
            len(entities),
            jurisdiction_name,
        )

        if data_source == "elms":
            all_projects_for_source = ALL_SCORECARD_PROJECTS
            lookups = elms_lookups
        else:
            all_projects_for_source = ALL_IL_PROJECTS_TO_REFRESH
            lookups = il_lookups

        group_projects = [
            p for p in all_projects_for_source if p["base_slug"] in base_slugs
        ]

        for project_def in group_projects:
            base_slug = str(project_def["base_slug"])
            slug = slug_prefix + base_slug

            project = await project_service.get_project_by_slug(slug)
            if project is None:
                logger.warning(
                    "Project slug '%s' not found in DB. Run import_scorecard_projects first.",
                    slug,
                )
                errors += 1
                continue

            status_lookup = lookups.get(base_slug, {})
            import_type = str(project_def["import_type"])
            preferred_status = EntityStatus(project_def["preferred_status"])

            default_status = (
                EntityStatus.NEUTRAL
                if import_type == "sponsorship"
                else EntityStatus.UNKNOWN
            )

            paired_vote_lookup: dict[str, EntityStatus] = {}
            if data_source == "elms" and import_type == "sponsorship":
                paired_vote_lookup = elms_vote_data_by_guid.get(
                    str(project_def["matter_guid"]), {}
                )

            for entity in entities:
                if data_source == "elms":
                    normalized_name = normalize_name(entity.name)
                else:
                    normalized_name = normalize_il_name(entity.name)

                entity_status = status_lookup.get(normalized_name, default_status)

                # For sponsorship projects where the group opposes the bill, flip cosponsors
                # to solid_disapproval so they render red instead of green.
                if (
                    import_type == "sponsorship"
                    and preferred_status == EntityStatus.SOLID_DISAPPROVAL
                    and normalized_name in status_lookup
                ):
                    entity_status = EntityStatus.SOLID_DISAPPROVAL

                # If paired vote data exists and this entity isn't in it, they weren't
                # serving at the time — override to UNKNOWN.
                if paired_vote_lookup and normalized_name not in paired_vote_lookup:
                    entity_status = EntityStatus.UNKNOWN

                status_record = EntityStatusRecord(
                    entity_id=entity.id,
                    project_id=project.id,
                    status=entity_status,
                    updated_by="admin",
                )
                try:
                    await status_service.create_status_record(status_record)
                    updated += 1
                except Exception:
                    logger.exception(
                        "Failed to upsert status record for entity %s / project %s",
                        entity.id,
                        project.id,
                    )
                    errors += 1

    logger.info("Scorecard refresh complete. Updated: %d, Errors: %d", updated, errors)
    return {"updated": updated, "errors": errors}


async def _fetch_elms_lookups() -> tuple[dict[str, dict[str, EntityStatus]], int]:
    """Fetch all ELMS matters and return per-base_slug lookup dicts."""
    matter_to_projects: dict[str, list[dict[str, Any]]] = {}
    for project_def in ALL_SCORECARD_PROJECTS:
        guid = str(project_def["matter_guid"])
        matter_to_projects.setdefault(guid, []).append(project_def)

    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    matter_cache: dict[str, dict[str, Any]] = {}

    async with aiohttp.ClientSession() as session:
        tasks = [_fetch_matter(session, semaphore, guid) for guid in matter_to_projects]
        for matter_guid, matter_data in await asyncio.gather(*tasks):
            if matter_data is not None:
                matter_cache[matter_guid] = matter_data
            else:
                logger.warning("Skipping ELMS matter %s (no data)", matter_guid)

    lookups: dict[str, dict[str, EntityStatus]] = {}
    errors = 0
    for project_def in ALL_SCORECARD_PROJECTS:
        base_slug = str(project_def["base_slug"])
        guid = str(project_def["matter_guid"])
        import_type = str(project_def["import_type"])

        matter = matter_cache.get(guid)
        if matter is None:
            logger.warning("No matter data for %s; skipping.", base_slug)
            lookups[base_slug] = {}
            errors += 1
            continue

        lookups[base_slug] = _extract_elms_lookup(matter, import_type, base_slug)

    return lookups, errors


async def _fetch_il_lookups() -> tuple[dict[str, dict[str, EntityStatus]], int]:
    """Fetch all OpenStates IL bills and return per-base_slug lookup dicts."""
    api_key = settings.OPENSTATES_API_KEY
    if not api_key:
        logger.warning(
            "OPENSTATES_API_KEY not set; skipping IL scorecard refresh. "
            "Set it in your environment to enable IL data refresh."
        )
        return {}, 0

    client = OpenStateBillsClient(api_key=api_key)
    # IL is rate-limited to 10 req/min — keep concurrency at 1
    semaphore = asyncio.Semaphore(1)

    # Deduplicate by (bill_identifier, import_type)
    unique_fetches: set[tuple[str, str]] = {
        (str(p["bill_identifier"]), str(p["import_type"]))
        for p in ALL_IL_PROJECTS_TO_REFRESH
    }
    logger.info(
        "Fetching %d unique IL bill(s) from OpenStates for %d projects",
        len(unique_fetches),
        len(ALL_IL_PROJECTS_TO_REFRESH),
    )

    tasks = [
        _fetch_il_bill(semaphore, client, bill_identifier, import_type)
        for bill_identifier, import_type in unique_fetches
    ]

    bill_cache: dict[tuple[str, str], dict[str, Any]] = {}
    for bill_identifier, import_type, bill_data in await asyncio.gather(*tasks):
        if bill_data is not None:
            bill_cache[(bill_identifier, import_type)] = bill_data
        else:
            logger.warning(
                "Skipping IL bill %s (%s) — no data", bill_identifier, import_type
            )

    lookups: dict[str, dict[str, EntityStatus]] = {}
    errors = 0
    for project_def in ALL_IL_SCORECARD_PROJECTS:
        base_slug = str(project_def["base_slug"])
        bill_identifier = str(project_def["bill_identifier"])
        import_type = str(project_def["import_type"])

        bill = bill_cache.get((bill_identifier, import_type))
        if bill is None:
            logger.warning("No bill data for %s; storing empty dict.", base_slug)
            lookups[base_slug] = {}
            errors += 1
            continue

        chamber = str(project_def.get("chamber", ""))
        vote_date = str(project_def.get("vote_date", ""))
        lookups[base_slug] = _extract_il_lookup(
            bill, import_type, base_slug, chamber=chamber, vote_date=vote_date
        )

    return lookups, errors
