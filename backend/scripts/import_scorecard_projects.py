"""Import script for seeding scorecard projects and populating EntityStatusRecords.

Run with:
    python -m scripts.import_scorecard_projects

Requires Chicago City Council jurisdiction and alderperson entities to be
already imported (run import_data chicago first).

Two groups are seeded:
  - Strong Towns Chicago: ADU, Parking, Single Stair, CHA Housing
  - Abundant Housing Illinois: all of the above + HED Bond, NWPO, Green Social Housing
"""

import asyncio
import logging
from typing import Any

from app.data.elms_scorecard_data import ELMS_SCORECARD_DATA
from app.imports.sources.chicago_city_clerk_elms import normalize_name
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

# All project definitions. Use "base_slug" — each group may prefix it.
ALL_SCORECARD_PROJECTS: list[dict[str, Any]] = [
    {
        "base_slug": "single-stair-ordinance",
        "title": "Single Stair Ordinance — Cosponsors",
        "description": (
            "Introduced by Ald. Matt Martin (47), this ordinance would allow new residential "
            "buildings up to 6 stories to use a single exit stairwell (paired with a "
            "fire-rated elevator), reducing construction costs and enabling more efficient "
            "floor plans for small-to-mid-rise apartments. Currently in committee. "
            "Source: https://chicityclerkelms.chicago.gov/Matter/?matterId=9F0FF51D-7036-F011-8C4D-001DD8309E73"
        ),
        "matter_guid": "9F0FF51D-7036-F011-8C4D-001DD8309E73",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": {
            "solid_approval": "Cosponsored",
            "neutral": "Not a Cosponsor",
            "unknown": "Not in Office",
        },
    },
    {
        "base_slug": "cha-housing-ordinance",
        "title": "CHA Housing Ordinance — Cosponsors",
        "description": (
            "Introduced by Ald. Matt Martin (47), this ordinance would prohibit the "
            "Department of Housing from holding affordable housing to higher design and "
            "construction standards than market-rate buildings — specifically eliminating "
            "the Architectural Technical Standards Manual (ATSM) applied to LIHTC-funded "
            "projects. It also sets a 10-day deadline for change order approvals during "
            "construction. Currently in committee. "
            "Source: https://chicityclerkelms.chicago.gov/Matter/?matterId=7F84A4EE-7136-F011-8C4D-001DD8309E73"
        ),
        "matter_guid": "7F84A4EE-7136-F011-8C4D-001DD8309E73",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": {
            "solid_approval": "Cosponsored",
            "neutral": "Not a Cosponsor",
            "unknown": "Not in Office",
        },
    },
    {
        "base_slug": "adu-citywide-vote",
        "title": "ADU Citywide Expansion — Vote",
        "description": (
            "Passed September 2025, this ordinance re-legalized accessory dwelling units "
            "(coach houses, basement apartments, granny flats) citywide — though each "
            "alderperson must separately opt their ward in. "
            "Source: https://chicityclerkelms.chicago.gov/Matter/?matterId=54028B60-C4FC-EE11-A1FE-001DD804AF4C"
        ),
        "matter_guid": "54028B60-C4FC-EE11-A1FE-001DD804AF4C",
        "import_type": "vote",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": {
            "solid_approval": "Voted Yes",
            "solid_disapproval": "Voted No",
            "neutral": "Absent/Not Voting",
            "unknown": "Not in Office",
        },
    },
    {
        "base_slug": "adu-citywide-sponsorship",
        "title": "ADU Citywide Expansion — Cosponsors",
        "description": (
            "Passed September 2025, this ordinance re-legalized accessory dwelling units "
            "(coach houses, basement apartments, granny flats) citywide — though each "
            "alderperson must separately opt their ward in. "
            "Source: https://chicityclerkelms.chicago.gov/Matter/?matterId=54028B60-C4FC-EE11-A1FE-001DD804AF4C"
        ),
        "matter_guid": "54028B60-C4FC-EE11-A1FE-001DD804AF4C",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": {
            "solid_approval": "Cosponsored",
            "neutral": "Not a Cosponsor",
            "unknown": "Not in Office",
        },
    },
    {
        "base_slug": "no-parking-minimums-vote",
        "title": "No Parking Minimums — Vote",
        "description": (
            "Sponsored by Ald. La Spata (1) and passed unanimously in July 2025, this "
            "ordinance allows developers to eliminate off-street parking requirements for "
            "new construction within Transit-Served Locations — defined as within half a "
            "mile of a CTA/Metra rail station or a quarter mile of major CTA bus corridors "
            "(covering roughly three-quarters of the city). "
            "Source: https://chicityclerkelms.chicago.gov/Matter/?matterId=06383958-E5EE-EF11-BE20-001DD83045C9"
        ),
        "matter_guid": "06383958-E5EE-EF11-BE20-001DD83045C9",
        "import_type": "vote",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": {
            "solid_approval": "Voted Yes",
            "solid_disapproval": "Voted No",
            "neutral": "Absent/Not Voting",
            "unknown": "Not in Office",
        },
    },
    {
        "base_slug": "no-parking-minimums-sponsorship",
        "title": "No Parking Minimums — Cosponsors",
        "description": (
            "Sponsored by Ald. La Spata (1) and passed unanimously in July 2025, this "
            "ordinance allows developers to eliminate off-street parking requirements for "
            "new construction within Transit-Served Locations — defined as within half a "
            "mile of a CTA/Metra rail station or a quarter mile of major CTA bus corridors "
            "(covering roughly three-quarters of the city). "
            "Source: https://chicityclerkelms.chicago.gov/Matter/?matterId=06383958-E5EE-EF11-BE20-001DD83045C9"
        ),
        "matter_guid": "06383958-E5EE-EF11-BE20-001DD83045C9",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": {
            "solid_approval": "Cosponsored",
            "neutral": "Not a Cosponsor",
            "unknown": "Not in Office",
        },
    },
    {
        "base_slug": "hed-bond-vote",
        "title": "HED Bond — Vote",
        "description": (
            "Sponsored by Mayor Brandon Johnson and passed 35-13 in April 2024, this "
            "ordinance authorized $1.25 billion in bonds over five years for affordable "
            "housing construction and neighborhood economic development, prioritizing "
            "historically underinvested South and West Side communities. A $135 million "
            "portion seeded the Green Social Housing revolving loan fund. "
            "Source: https://chicityclerkelms.chicago.gov/Matter/?matterId=7A924B08-39D0-EE11-9078-001DD806E058"
        ),
        "matter_guid": "7A924B08-39D0-EE11-9078-001DD806E058",
        "import_type": "vote",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": {
            "solid_approval": "Voted Yes",
            "solid_disapproval": "Voted No",
            "neutral": "Absent/Not Voting",
            "unknown": "Not in Office",
        },
    },
    {
        "base_slug": "hed-bond-sponsorship",
        "title": "HED Bond — Cosponsors",
        "description": (
            "Sponsored by Mayor Brandon Johnson and passed 35-13 in April 2024, this "
            "ordinance authorized $1.25 billion in bonds over five years for affordable "
            "housing construction and neighborhood economic development, prioritizing "
            "historically underinvested South and West Side communities. A $135 million "
            "portion seeded the Green Social Housing revolving loan fund. "
            "Source: https://chicityclerkelms.chicago.gov/Matter/?matterId=7A924B08-39D0-EE11-9078-001DD806E058"
        ),
        "matter_guid": "7A924B08-39D0-EE11-9078-001DD806E058",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": {
            "solid_approval": "Cosponsored",
            "neutral": "Not a Cosponsor",
            "unknown": "Not in Office",
        },
    },
    {
        "base_slug": "nwpo-vote",
        "title": "Northwest Side Preservation Ordinance — Vote",
        "description": (
            "Led by Ald. Ramirez-Rosa (35) and passed 41-3 in September 2024, this "
            "ordinance raised demolition surcharges to $20,000/unit in neighborhoods "
            "around the 606 trail corridor and established a Tenant Opportunity to "
            "Purchase program giving tenants first refusal when their building is listed "
            "for sale. "
            "Source: https://chicityclerkelms.chicago.gov/Matter/?matterId=C3F5E354-5F44-EF11-8409-001DD8306DF0"
        ),
        "matter_guid": "C3F5E354-5F44-EF11-8409-001DD8306DF0",
        "import_type": "vote",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": {
            "solid_approval": "Voted Yes",
            "solid_disapproval": "Voted No",
            "neutral": "Absent/Not Voting",
            "unknown": "Not in Office",
        },
    },
    {
        "base_slug": "nwpo-sponsorship",
        "title": "Northwest Side Preservation Ordinance — Cosponsors",
        "description": (
            "Led by Ald. Ramirez-Rosa (35) and passed 41-3 in September 2024, this "
            "ordinance raised demolition surcharges to $20,000/unit in neighborhoods "
            "around the 606 trail corridor and established a Tenant Opportunity to "
            "Purchase program giving tenants first refusal when their building is listed "
            "for sale. "
            "Source: https://chicityclerkelms.chicago.gov/Matter/?matterId=C3F5E354-5F44-EF11-8409-001DD8306DF0"
        ),
        "matter_guid": "C3F5E354-5F44-EF11-8409-001DD8306DF0",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": {
            "solid_approval": "Cosponsored",
            "neutral": "Not a Cosponsor",
            "unknown": "Not in Office",
        },
    },
    {
        "base_slug": "gsh-vote",
        "title": "Green Social Housing — Vote",
        "description": (
            "Sponsored by Mayor Johnson and passed 33-13 in May 2025, this ordinance "
            "created the Residential Investment Corporation (RIC) — a public entity that "
            "develops permanently affordable, mixed-income housing by retaining ownership "
            "stakes in joint ventures with private developers. Funded by a $135 million "
            "revolving loan fund from the 2024 HED Bond. Chicago is the first major U.S. "
            "city to adopt this model. "
            "Source: https://chicityclerkelms.chicago.gov/Matter/?matterId=76EEBA20-D3EE-EF11-BE20-001DD83045C9"
        ),
        "matter_guid": "76EEBA20-D3EE-EF11-BE20-001DD83045C9",
        "import_type": "vote",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": {
            "solid_approval": "Voted Yes",
            "solid_disapproval": "Voted No",
            "neutral": "Absent/Not Voting",
            "unknown": "Not in Office",
        },
    },
    {
        "base_slug": "gsh-sponsorship",
        "title": "Green Social Housing — Cosponsors",
        "description": (
            "Sponsored by Mayor Johnson and passed 33-13 in May 2025, this ordinance "
            "created the Residential Investment Corporation (RIC) — a public entity that "
            "develops permanently affordable, mixed-income housing by retaining ownership "
            "stakes in joint ventures with private developers. Funded by a $135 million "
            "revolving loan fund from the 2024 HED Bond. Chicago is the first major U.S. "
            "city to adopt this model. "
            "Source: https://chicityclerkelms.chicago.gov/Matter/?matterId=76EEBA20-D3EE-EF11-BE20-001DD83045C9"
        ),
        "matter_guid": "76EEBA20-D3EE-EF11-BE20-001DD83045C9",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": {
            "solid_approval": "Cosponsored",
            "neutral": "Not a Cosponsor",
            "unknown": "Not in Office",
        },
    },
]

# Strong Towns Chicago: ADU, Parking, Single Stair, CHA Housing (no HED, NWPO, GSH)
STC_BASE_SLUGS = {
    "single-stair-ordinance",
    "cha-housing-ordinance",
    "adu-citywide-vote",
    "adu-citywide-sponsorship",
    "no-parking-minimums-vote",
    "no-parking-minimums-sponsorship",
}

# Abundant Housing Illinois: all projects
AHIL_BASE_SLUGS = {p["base_slug"] for p in ALL_SCORECARD_PROJECTS}

GROUP_CONFIG: list[dict[str, Any]] = [
    {
        "name": "Strong Towns Chicago",
        "description": "Empowers neighborhoods to incrementally build a more financially resilient city.",
        "base_slugs": STC_BASE_SLUGS,
        "slug_prefix": "",
    },
    {
        "name": "Abundant Housing Illinois",
        "description": "Advocates for more homes in more places across Illinois.",
        "base_slugs": AHIL_BASE_SLUGS,
        "slug_prefix": "ahil-",
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

    entities = await entity_service.list_entities(jurisdiction_id=jurisdiction.id)
    logger.info("Found %d alderpersons.", len(entities))

    # Pre-build vote ELMS data keyed by matter_guid so sponsorship projects can
    # detect "not in office": if an alder is absent from the vote roll call they
    # were not serving, and should be UNKNOWN for cosponsorship too.
    vote_data_by_guid: dict[str, dict[str, EntityStatus]] = {}
    for pd in ALL_SCORECARD_PROJECTS:
        if pd["import_type"] == "vote":
            raw = ELMS_SCORECARD_DATA.get(str(pd["base_slug"])) or {}
            vote_data_by_guid[str(pd["matter_guid"])] = {
                name: EntityStatus(status) for name, status in raw.items()
            }

    total_created = 0
    total_found = 0

    for group_cfg in GROUP_CONFIG:
        group = await group_service.find_or_create_by_name(
            str(group_cfg["name"]),
            str(group_cfg["description"]),
        )
        logger.info("Processing group: %s (%s)", group.name, group.id)

        slug_prefix = str(group_cfg["slug_prefix"])
        base_slugs: set[str] = group_cfg["base_slugs"]  # type: ignore[assignment]
        group_projects = [
            p for p in ALL_SCORECARD_PROJECTS if p["base_slug"] in base_slugs
        ]

        for project_def in group_projects:
            base_slug = str(project_def["base_slug"])
            slug = slug_prefix + base_slug
            logger.info("Processing project: %s (group: %s)", slug, group.name)

            # Idempotency: check for existing project by slug
            existing_project = await project_service.get_project_by_slug(slug)
            if existing_project:
                project = existing_project
                total_found += 1
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
                total_created += 1
                logger.info("Created project: %s (%s)", slug, project.id)

            # Look up pre-fetched ELMS data from the static cache
            elms_raw = ELMS_SCORECARD_DATA.get(base_slug)
            if elms_raw is None:
                logger.warning(
                    "No cache entry for '%s'. Run scripts/fetch_elms_scorecard_data.py "
                    "to regenerate app/data/elms_scorecard_data.py.",
                    base_slug,
                )
                elms_raw = {}
            elms_lookup: dict[str, EntityStatus] = {
                name: EntityStatus(status) for name, status in elms_raw.items()
            }

            import_type = str(project_def["import_type"])
            # Sponsorship cache only contains cosponsors; absent alders weren't
            # out of office — they just didn't cosponsor. Vote data includes everyone
            # who was serving, so missing from vote cache → not in office.
            default_status = (
                EntityStatus.NEUTRAL
                if import_type == "sponsorship"
                else EntityStatus.UNKNOWN
            )

            # For sponsorship projects, use the paired vote roll call (same matter_guid)
            # to distinguish "not a cosponsor" (NEUTRAL) from "not in office" (UNKNOWN).
            # The vote record includes every alder who was serving; anyone absent from it
            # was not yet in office and should be UNKNOWN for cosponsorship too.
            paired_vote_lookup: dict[str, EntityStatus] = {}
            if import_type == "sponsorship":
                paired_vote_lookup = vote_data_by_guid.get(
                    str(project_def["matter_guid"]), {}
                )

            matched = 0
            unmatched = 0
            for entity in entities:
                normalized_entity_name = normalize_name(entity.name)
                entity_status = elms_lookup.get(normalized_entity_name, default_status)

                # If paired vote data exists and this alder isn't in it, they weren't
                # serving at the time — override the sponsorship status to UNKNOWN.
                if (
                    paired_vote_lookup
                    and normalized_entity_name not in paired_vote_lookup
                ):
                    entity_status = EntityStatus.UNKNOWN

                if normalized_entity_name not in elms_lookup:
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
