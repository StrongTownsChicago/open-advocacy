"""Scorecard refresh service: fetch live eLMS data and upsert EntityStatusRecords.

This module provides `run_scorecard_refresh()`, which fetches current vote and
sponsorship data from the Chicago City Clerk eLMS API and upserts
EntityStatusRecord rows for all scorecard projects.

This is the runtime equivalent of running:
    python -m scripts.fetch_elms_scorecard_data   (fetch + write static file)
    python -m scripts.import_scorecard_projects    (read static file + upsert)

But without the intermediate static file step.
"""

import asyncio
import logging
from typing import Any

import aiohttp

from app.imports.sources.chicago_city_clerk_elms import (
    ELMSClient,
    normalize_name,
    vote_value_to_entity_status,
)
from app.models.pydantic.models import EntityStatus, EntityStatusRecord
from app.services.entity_service import EntityService
from app.services.jurisdiction_service import JurisdictionService
from app.services.project_service import ProjectService
from app.services.status_service import StatusService
from scripts.import_scorecard_projects import ALL_SCORECARD_PROJECTS, GROUP_CONFIG

logger = logging.getLogger(__name__)

MAX_CONCURRENT = 3


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


def _extract_lookup(
    matter: dict[str, Any],
    import_type: str,
    base_slug: str,
) -> dict[str, str]:
    """Extract a {normalized_name: entity_status_value} dict from a matter.

    Copied from scripts/fetch_elms_scorecard_data.py to avoid a scripts→app
    import boundary violation. Both copies should remain in sync.
    """
    client = ELMSClient()
    if import_type == "vote":
        votes = client.extract_votes(matter)
        if votes is None:
            logger.warning("No final passage vote found for %s", base_slug)
            return {}
        return {
            normalize_name(str(v["voterName"])): vote_value_to_entity_status(
                str(v.get("vote", ""))
            ).value
            for v in votes
            if v.get("voterName")
        }
    else:
        # sponsorship
        sponsors = client.extract_sponsors(matter)
        return {
            normalize_name(str(s["sponsorName"])): EntityStatus.SOLID_APPROVAL.value
            for s in sponsors
            if s.get("sponsorName")
        }


async def run_scorecard_refresh(
    entity_service: EntityService,
    jurisdiction_service: JurisdictionService,
    project_service: ProjectService,
    status_service: StatusService,
) -> dict[str, int]:
    """Fetch live eLMS data and upsert EntityStatusRecords for all scorecard projects.

    Returns a dict with keys:
      - "updated": number of status records successfully upserted
      - "errors": number of failures (missing projects, missing matters, etc.)
    """
    # Only process ELMS (Chicago) groups — IL groups do not have a runtime refresh yet.
    elms_groups = [g for g in GROUP_CONFIG if g.get("data_source", "elms") == "elms"]

    jurisdiction_name = "Chicago City Council"
    jurisdiction = await jurisdiction_service.find_by_name(jurisdiction_name)
    if not jurisdiction:
        raise ValueError(
            f"{jurisdiction_name} jurisdiction not found. Run import_data chicago first."
        )

    entities = await entity_service.list_entities(jurisdiction_id=jurisdiction.id)
    logger.info("Found %d alderpersons for refresh.", len(entities))

    # Collect unique matter GUIDs from ELMS projects only
    matter_to_projects: dict[str, list[dict[str, Any]]] = {}
    for project_def in ALL_SCORECARD_PROJECTS:
        guid = str(project_def["matter_guid"])
        matter_to_projects.setdefault(guid, []).append(project_def)

    # Fetch all matters concurrently with bounded parallelism
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    matter_cache: dict[str, dict[str, Any]] = {}

    async with aiohttp.ClientSession() as session:
        tasks = [_fetch_matter(session, semaphore, guid) for guid in matter_to_projects]
        for matter_guid, matter_data in await asyncio.gather(*tasks):
            if matter_data is not None:
                matter_cache[matter_guid] = matter_data
            else:
                logger.warning("Skipping matter %s (no data)", matter_guid)

    # Build per-base_slug lookup dicts from the fetched matter data
    elms_lookups: dict[str, dict[str, EntityStatus]] = {}
    fetch_errors = 0
    for project_def in ALL_SCORECARD_PROJECTS:
        base_slug = str(project_def["base_slug"])
        guid = str(project_def["matter_guid"])
        import_type = str(project_def["import_type"])

        matter = matter_cache.get(guid)
        if matter is None:
            logger.warning("No matter data for %s; skipping.", base_slug)
            elms_lookups[base_slug] = {}
            fetch_errors += 1
            continue

        raw = _extract_lookup(matter, import_type, base_slug)
        elms_lookups[base_slug] = {
            name: EntityStatus(status) for name, status in raw.items()
        }

    # Pre-build vote lookups keyed by matter_guid for "not in office" detection
    # on paired sponsorship projects.
    vote_data_by_guid: dict[str, dict[str, EntityStatus]] = {}
    for project_def in ALL_SCORECARD_PROJECTS:
        if project_def["import_type"] == "vote":
            base_slug = str(project_def["base_slug"])
            vote_data_by_guid[str(project_def["matter_guid"])] = elms_lookups.get(
                base_slug, {}
            )

    updated = 0
    errors = fetch_errors

    for group_cfg in elms_groups:
        slug_prefix = str(group_cfg["slug_prefix"])
        base_slugs: set[str] = group_cfg["base_slugs"]  # type: ignore[assignment]
        group_projects = [
            p for p in ALL_SCORECARD_PROJECTS if p["base_slug"] in base_slugs
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

            elms_lookup = elms_lookups.get(base_slug, {})
            import_type = str(project_def["import_type"])

            default_status = (
                EntityStatus.NEUTRAL
                if import_type == "sponsorship"
                else EntityStatus.UNKNOWN
            )

            paired_vote_lookup: dict[str, EntityStatus] = {}
            if import_type == "sponsorship":
                paired_vote_lookup = vote_data_by_guid.get(
                    str(project_def["matter_guid"]), {}
                )

            for entity in entities:
                normalized_entity_name = normalize_name(entity.name)
                entity_status = elms_lookup.get(normalized_entity_name, default_status)

                # If paired vote data exists and this alder isn't in it, they were
                # not serving at the time — override the sponsorship status to UNKNOWN.
                if (
                    paired_vote_lookup
                    and normalized_entity_name not in paired_vote_lookup
                ):
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
