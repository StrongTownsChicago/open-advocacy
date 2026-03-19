"""Import script for seeding scorecard projects and populating EntityStatusRecords.

Run with:
    python -m scripts.import_scorecard_projects

Requires jurisdiction entities to be already imported:
  - Chicago: run import_data chicago first
  - Illinois: run import_data illinois first

Four groups are seeded:
  - Strong Towns Chicago: ADU, Parking, Single Stair, CHA Housing
  - Abundant Housing Illinois: all of the above + HED Bond, NWPO, Green Social Housing
  - Abundant Housing Illinois — IL House: IL House housing bills
  - Abundant Housing Illinois — IL Senate: IL Senate housing bills
"""

import asyncio
import logging

from app.data.elms_scorecard_data import ELMS_SCORECARD_DATA
from app.data.il_scorecard_data import IL_SCORECARD_DATA
from app.imports.sources.chicago_city_clerk_elms import normalize_name
from app.imports.sources.openstates import normalize_il_name
from app.models.pydantic.models import (
    DashboardConfig,
    EntityStatus,
    EntityStatusRecord,
    ProjectBase,
    ProjectStatus,
)
from app.services.service_factory import (
    get_cached_entity_service,
    get_cached_group_service,
    get_cached_jurisdiction_service,
    get_cached_project_service,
    get_cached_status_service,
)
from scripts.scorecard_project_data import (
    ALL_IL_SCORECARD_PROJECTS,
    ALL_SCORECARD_PROJECTS,
    GROUP_CONFIG,
    STC_ONLY_IL_SCORECARD_PROJECTS,
)

# ---------------------------------------------------------------------------
# Import logic helpers
# ---------------------------------------------------------------------------


def _get_entity_status_lookup(
    base_slug: str,
    data_source: str,
    logger: logging.Logger,
) -> dict[str, EntityStatus]:
    """Return a {normalized_name: EntityStatus} lookup for a project's data source.

    For ELMS (Chicago) projects, reads from ELMS_SCORECARD_DATA.
    For IL OpenStates projects, reads from IL_SCORECARD_DATA.
    Logs a warning if the base_slug has no cached entry.
    """
    if data_source == "elms":
        raw = ELMS_SCORECARD_DATA.get(base_slug)
        if raw is None:
            logger.warning(
                "No ELMS cache entry for '%s'. Run scripts/fetch_elms_scorecard_data.py.",
                base_slug,
            )
            raw = {}
        return {name: EntityStatus(status) for name, status in raw.items()}
    else:
        # il_openstates
        raw = IL_SCORECARD_DATA.get(base_slug)
        if raw is None:
            logger.warning(
                "No IL OpenStates cache entry for '%s'. "
                "Run scripts/fetch_openstates_il_scorecard_data.py.",
                base_slug,
            )
            raw = {}
        return {name: EntityStatus(status) for name, status in raw.items()}


def _normalize_entity_name(entity_name: str, data_source: str) -> str:
    """Normalize an entity name using the appropriate normalizer for the data source."""
    if data_source == "elms":
        return normalize_name(entity_name)
    return normalize_il_name(entity_name)


# ---------------------------------------------------------------------------
# Main import function
# ---------------------------------------------------------------------------


async def import_scorecard_projects() -> None:
    """Seed scorecard projects and populate EntityStatusRecords from cached data."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("scorecard-import")

    jurisdiction_service = get_cached_jurisdiction_service()
    entity_service = get_cached_entity_service()
    project_service = get_cached_project_service()
    group_service = get_cached_group_service()
    status_service = get_cached_status_service()

    total_created = 0
    total_found = 0

    for group_cfg in GROUP_CONFIG:
        group_name = str(group_cfg["name"])
        jurisdiction_name = str(group_cfg["jurisdiction_name"])
        data_source = str(group_cfg["data_source"])
        representative_title = str(group_cfg["representative_title"])
        slug_prefix = str(group_cfg["slug_prefix"])
        base_slugs: set[str] = group_cfg["base_slugs"]  # type: ignore[assignment]

        jurisdiction = await jurisdiction_service.find_by_name(jurisdiction_name)
        if not jurisdiction:
            logger.error(
                "Jurisdiction '%s' not found for group '%s'. "
                "Run the appropriate import_data command first.",
                jurisdiction_name,
                group_name,
            )
            continue

        entities = await entity_service.list_entities(jurisdiction_id=jurisdiction.id)
        logger.info(
            "Group '%s': found %d entities in '%s'.",
            group_name,
            len(entities),
            jurisdiction_name,
        )

        # Determine the correct project list for this group's data source.
        # STC groups may include STC-only bills not in the AHIL/shared list.
        if data_source == "elms":
            all_projects_for_source = ALL_SCORECARD_PROJECTS
        else:
            all_projects_for_source = (
                ALL_IL_SCORECARD_PROJECTS + STC_ONLY_IL_SCORECARD_PROJECTS
            )

        group_projects = [
            p for p in all_projects_for_source if p["base_slug"] in base_slugs
        ]

        # Pre-build vote lookup for ELMS sponsorship "not in office" detection
        vote_data_by_guid: dict[str, dict[str, EntityStatus]] = {}
        if data_source == "elms":
            for pd in group_projects:
                if pd["import_type"] == "vote":
                    raw = ELMS_SCORECARD_DATA.get(str(pd["base_slug"])) or {}
                    vote_data_by_guid[str(pd["matter_guid"])] = {
                        name: EntityStatus(status) for name, status in raw.items()
                    }

        group = await group_service.find_or_create_by_name(
            group_name,
            str(group_cfg["description"]),
        )
        logger.info("Processing group: %s (%s)", group.name, group.id)

        for project_def in group_projects:
            base_slug = str(project_def["base_slug"])
            slug = slug_prefix + base_slug
            logger.info("Processing project: %s (group: %s)", slug, group.name)

            position: int | None = project_def.get("position")  # type: ignore[assignment]

            # Idempotency: check for existing project by slug
            existing_project = await project_service.get_project_by_slug(slug)
            if existing_project:
                project = existing_project
                total_found += 1
                logger.info("Project already exists: %s (%s)", slug, project.id)
                # Update position if it has changed
                existing_position = (
                    existing_project.dashboard_config.position
                    if existing_project.dashboard_config
                    else None
                )
                if existing_position != position:
                    updated_config = DashboardConfig(
                        representative_title=representative_title,
                        status_labels=project_def["status_labels"],
                        position=position,
                    )
                    await project_service.update_project(
                        existing_project.id,
                        ProjectBase(
                            title=existing_project.title,
                            description=existing_project.description,
                            status=existing_project.status,
                            active=existing_project.active,
                            preferred_status=existing_project.preferred_status,
                            jurisdiction_id=existing_project.jurisdiction_id,
                            group_id=existing_project.group_id,
                            created_by=existing_project.created_by or "admin",
                            slug=existing_project.slug,
                            dashboard_config=updated_config,
                        ),
                    )
                    logger.info(
                        "Updated position for %s: %s → %s",
                        slug,
                        existing_position,
                        position,
                    )
            else:
                project = await project_service.create_project(
                    ProjectBase(
                        title=str(project_def["title"]),
                        description=str(project_def["description"]),
                        status=ProjectStatus.ACTIVE,
                        active=True,
                        preferred_status=project_def["preferred_status"],
                        jurisdiction_id=jurisdiction.id,
                        group_id=group.id,
                        created_by="admin",
                        slug=slug,
                        dashboard_config=DashboardConfig(
                            representative_title=representative_title,
                            status_labels=project_def["status_labels"],
                            position=position,
                        ),
                    )
                )
                total_created += 1
                logger.info("Created project: %s (%s)", slug, project.id)

            # Look up cached data for this project
            status_lookup = _get_entity_status_lookup(base_slug, data_source, logger)

            import_type = str(project_def["import_type"])
            preferred_status = EntityStatus(project_def["preferred_status"])
            # Sponsorship cache only contains cosponsors; absent legislators didn't
            # cosponsor but were not necessarily out of office.
            # For ELMS: vote data determines "not in office" (UNKNOWN).
            # For IL OpenStates: most bills are in committee — no vote data yet,
            # so missing from sponsorship cache → NEUTRAL (not a cosponsor).
            default_status = (
                EntityStatus.NEUTRAL
                if import_type == "sponsorship"
                else EntityStatus.UNKNOWN
            )

            # For ELMS sponsorship projects, use the paired vote roll call to detect
            # "not in office" (anyone absent from the vote was not serving).
            paired_vote_lookup: dict[str, EntityStatus] = {}
            if data_source == "elms" and import_type == "sponsorship":
                paired_vote_lookup = vote_data_by_guid.get(
                    str(project_def["matter_guid"]), {}
                )

            matched = 0
            unmatched = 0
            for entity in entities:
                normalized_entity_name = _normalize_entity_name(
                    entity.name, data_source
                )
                entity_status = status_lookup.get(
                    normalized_entity_name, default_status
                )

                # For sponsorship projects where the group opposes the bill, flip cosponsors
                # to solid_disapproval so they render red instead of green.
                if (
                    import_type == "sponsorship"
                    and preferred_status == EntityStatus.SOLID_DISAPPROVAL
                    and normalized_entity_name in status_lookup
                ):
                    entity_status = EntityStatus.SOLID_DISAPPROVAL

                # If paired vote data exists and this entity isn't in it, they weren't
                # serving at the time — override to UNKNOWN.
                if (
                    paired_vote_lookup
                    and normalized_entity_name not in paired_vote_lookup
                ):
                    entity_status = EntityStatus.UNKNOWN

                if normalized_entity_name not in status_lookup:
                    unmatched += 1
                    if unmatched <= 5:
                        logger.warning(
                            "Entity '%s' (normalized: '%s') not found in %s data for %s",
                            entity.name,
                            normalized_entity_name,
                            data_source,
                            slug,
                        )
                else:
                    matched += 1

                status_record = EntityStatusRecord(
                    entity_id=entity.id,
                    project_id=project.id,
                    status=entity_status,
                    updated_by="admin",
                )
                await status_service.create_status_record(status_record)

            logger.info(
                "Project %s: %d entities matched, %d unmatched (set to %s)",
                slug,
                matched,
                unmatched,
                default_status.value,
            )

    logger.info(
        "Scorecard import complete. Projects created: %d, already existed: %d.",
        total_created,
        total_found,
    )


if __name__ == "__main__":
    asyncio.run(import_scorecard_projects())
