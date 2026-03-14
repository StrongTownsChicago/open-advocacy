"""Import script for seeding scorecard projects and populating EntityStatusRecords.

Run with:
    python -m scripts.import_scorecard_projects

Requires Chicago City Council jurisdiction and alderperson entities to be
already imported (run import_data chicago first).
"""

import asyncio
import logging
from typing import Any

from app.imports.sources.chicago_city_clerk_elms import (
    ELMSClient,
    normalize_name,
    vote_value_to_entity_status,
)
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

SCORECARD_PROJECTS: list[dict[str, Any]] = [
    {
        "slug": "single-stair-ordinance",
        "title": "Single Stair Ordinance — Cosponsors",
        "description": (
            "The Single Stair Ordinance would allow multi-unit residential buildings "
            "up to 6 stories to be built with a single staircase, enabling more efficient "
            "floor plans and more housing. This tracks which alderpersons have cosponsored "
            "the ordinance."
        ),
        "matter_guid": "9F0FF51D-7036-F011-8C4D-001DD8309E73",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": {
            "solid_approval": "Cosponsored",
            "unknown": "Not a Cosponsor",
        },
    },
    {
        "slug": "cha-housing-ordinance",
        "title": "CHA Housing Ordinance — Cosponsors",
        "description": (
            "The CHA Housing Ordinance would expand affordable housing options by allowing "
            "Chicago Housing Authority units in more areas of the city. This tracks which "
            "alderpersons have cosponsored the ordinance."
        ),
        "matter_guid": "7F84A4EE-7136-F011-8C4D-001DD8309E73",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": {
            "solid_approval": "Cosponsored",
            "unknown": "Not a Cosponsor",
        },
    },
    {
        "slug": "adu-citywide-vote",
        "title": "ADU Citywide Expansion — Vote",
        "description": (
            "The ADU Citywide Expansion ordinance re-legalized accessory dwelling units "
            "(coach houses, basement apartments, granny flats) across Chicago. "
            "This tracks how each alderperson voted on final passage."
        ),
        "matter_guid": "54028B60-C4FC-EE11-A1FE-001DD804AF4C",
        "import_type": "vote",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": {
            "solid_approval": "Voted Yes",
            "solid_disapproval": "Voted No",
            "neutral": "Abstained",
            "unknown": "Absent/Not Voting",
        },
    },
    {
        "slug": "adu-citywide-sponsorship",
        "title": "ADU Citywide Expansion — Cosponsors",
        "description": (
            "The ADU Citywide Expansion ordinance re-legalized accessory dwelling units "
            "(coach houses, basement apartments, granny flats) across Chicago. "
            "This tracks which alderpersons cosponsored the ordinance."
        ),
        "matter_guid": "54028B60-C4FC-EE11-A1FE-001DD804AF4C",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": {
            "solid_approval": "Cosponsored",
            "unknown": "Not a Cosponsor",
        },
    },
    {
        "slug": "no-parking-minimums-vote",
        "title": "No Parking Minimums — Vote",
        "description": (
            "The No Parking Minimums ordinance eliminated mandatory parking minimums "
            "for new developments near transit, reducing construction costs and enabling "
            "more housing. This tracks how each alderperson voted on final passage."
        ),
        "matter_guid": "06383958-E5EE-EF11-BE20-001DD83045C9",
        "import_type": "vote",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": {
            "solid_approval": "Voted Yes",
            "solid_disapproval": "Voted No",
            "neutral": "Abstained",
            "unknown": "Absent/Not Voting",
        },
    },
    {
        "slug": "no-parking-minimums-sponsorship",
        "title": "No Parking Minimums — Cosponsors",
        "description": (
            "The No Parking Minimums ordinance eliminated mandatory parking minimums "
            "for new developments near transit, reducing construction costs and enabling "
            "more housing. This tracks which alderpersons cosponsored the ordinance."
        ),
        "matter_guid": "06383958-E5EE-EF11-BE20-001DD83045C9",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": {
            "solid_approval": "Cosponsored",
            "unknown": "Not a Cosponsor",
        },
    },
    {
        "slug": "hed-bond-vote",
        "title": "HED Bond — Vote",
        "description": (
            "The Housing and Economic Development Bond provided funding for affordable "
            "housing and neighborhood development. This tracks how each alderperson "
            "voted on final passage."
        ),
        "matter_guid": "7A924B08-39D0-EE11-9078-001DD806E058",
        "import_type": "vote",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": {
            "solid_approval": "Voted Yes",
            "solid_disapproval": "Voted No",
            "neutral": "Abstained",
            "unknown": "Absent/Not Voting",
        },
    },
    {
        "slug": "hed-bond-sponsorship",
        "title": "HED Bond — Cosponsors",
        "description": (
            "The Housing and Economic Development Bond provided funding for affordable "
            "housing and neighborhood development. This tracks which alderpersons "
            "cosponsored the bond ordinance."
        ),
        "matter_guid": "7A924B08-39D0-EE11-9078-001DD806E058",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": {
            "solid_approval": "Cosponsored",
            "unknown": "Not a Cosponsor",
        },
    },
]


async def import_scorecard_projects() -> None:
    """Seed scorecard projects and populate EntityStatusRecords from ELMS data."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("scorecard-import")

    jurisdiction_service = get_cached_jurisdiction_service()
    entity_service = get_cached_entity_service()
    project_service = get_cached_project_service()
    group_service = get_cached_group_service()
    status_service = get_cached_status_service()

    jurisdiction = await jurisdiction_service.find_by_name("Chicago City Council")
    if not jurisdiction:
        logger.error(
            "Chicago City Council jurisdiction not found. Run import_data chicago first."
        )
        return

    group = await group_service.find_or_create_by_name(
        "Strong Towns Chicago",
        "Empowers neighborhoods to incrementally build a more financially resilient city.",
    )
    logger.info("Using group: %s (%s)", group.name, group.id)

    entities = await entity_service.list_entities(jurisdiction_id=jurisdiction.id)
    logger.info("Found %d alderpersons.", len(entities))

    client = ELMSClient()
    projects_created = 0
    projects_found = 0

    for project_def in SCORECARD_PROJECTS:
        slug = str(project_def["slug"])
        logger.info("Processing project: %s", slug)

        # Idempotency: check for existing project by slug
        existing_project = await project_service.get_project_by_slug(slug)
        if existing_project:
            project = existing_project
            projects_found += 1
            logger.info("Project already exists: %s (%s)", slug, project.id)
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
                        representative_title="Alderperson",
                        status_labels=project_def["status_labels"],
                    ),
                )
            )
            projects_created += 1
            logger.info("Created project: %s (%s)", slug, project.id)

        # Fetch ELMS data for this project (single API call returns full matter)
        matter_guid = str(project_def["matter_guid"])
        import_type = str(project_def["import_type"])

        matter = await client.get_matter(matter_guid)
        if matter is None:
            logger.warning(
                "Matter GUID %s not found in ELMS; skipping status import for %s",
                matter_guid,
                slug,
            )
            continue

        if import_type == "vote":
            votes = client.extract_votes(matter)
            if votes is None:
                logger.warning(
                    "No final passage vote found for matter %s (%s); skipping",
                    matter_guid,
                    slug,
                )
                continue
            elms_lookup: dict[str, EntityStatus] = {
                normalize_name(str(v["voterName"])): vote_value_to_entity_status(
                    str(v.get("vote", ""))
                )
                for v in votes
                if v.get("voterName")
            }
        else:
            # sponsorship
            sponsors = client.extract_sponsors(matter)
            elms_lookup: dict[str, EntityStatus] = {  # type: ignore[no-redef]
                normalize_name(str(s["sponsorName"])): EntityStatus.SOLID_APPROVAL
                for s in sponsors
                if s.get("sponsorName")
            }

        matched = 0
        unmatched = 0
        for entity in entities:
            normalized_entity_name = normalize_name(entity.name)
            entity_status = elms_lookup.get(
                normalized_entity_name, EntityStatus.UNKNOWN
            )

            if (
                entity_status == EntityStatus.UNKNOWN
                and normalized_entity_name not in elms_lookup
            ):
                unmatched += 1
                if unmatched <= 5:
                    logger.warning(
                        "Entity '%s' (normalized: '%s') not found in ELMS data for %s",
                        entity.name,
                        normalized_entity_name,
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
            "Project %s: %d entities matched, %d unmatched (set to UNKNOWN)",
            slug,
            matched,
            unmatched,
        )

    logger.info(
        "Scorecard import complete. Projects created: %d, already existed: %d.",
        projects_created,
        projects_found,
    )


if __name__ == "__main__":
    asyncio.run(import_scorecard_projects())
