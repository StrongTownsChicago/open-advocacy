import asyncio
import logging
from app.services.service_factory import (
    get_cached_jurisdiction_service,
    get_cached_entity_service,
    get_cached_project_service,
    get_cached_group_service,
    get_cached_status_service,
)
from app.data.ward_zoning_data import WARD_RS_ZONED_PCT
from app.models.pydantic.models import (
    DashboardConfig,
    MetricDisplayConfig,
    ProjectBase,
    EntityStatusRecord,
    EntityStatus,
    ProjectStatus,
)

WARD_OPT_IN_INFO = {
    1: {
        "type": "full",
        "block_limits": False,
        "homeowner_req": False,
        "admin_adj": False,
    },
    3: {
        "type": "not_eligible",
        "block_limits": False,
        "homeowner_req": False,
        "admin_adj": False,
        "notes": "not eligible (no SFH zoning to opt-in)",
    },
    4: {
        "type": "full",
        "block_limits": False,
        "homeowner_req": False,
        "admin_adj": False,
    },
    5: {
        "type": "full",
        "block_limits": False,
        "homeowner_req": False,
        "admin_adj": False,
    },
    6: {
        "type": "full",
        "notes": "Whole ward (including the part currently in the pilot)",
        "block_limits": True,
        "homeowner_req": True,
        "admin_adj": True,
    },
    12: {
        "type": "full",
        "block_limits": False,
        "homeowner_req": False,
        "admin_adj": False,
    },
    14: {
        "type": "partial",
        "notes": "Partial. Only precincts 1, 4, 9, and 15",
        "block_limits": True,
        "homeowner_req": True,
        "admin_adj": True,
    },
    22: {
        "type": "full",
        "block_limits": True,
        "homeowner_req": True,
        "admin_adj": True,
    },
    25: {
        "type": "full",
        "block_limits": True,
        "homeowner_req": True,
        "admin_adj": True,
    },
    26: {
        "type": "full",
        "block_limits": False,
        "homeowner_req": False,
        "admin_adj": False,
    },
    27: {
        "type": "full",
        "block_limits": False,
        "homeowner_req": False,
        "admin_adj": False,
    },
    29: {
        "type": "full",
        "block_limits": False,
        "homeowner_req": False,
        "admin_adj": False,
    },
    30: {
        "type": "partial",
        "notes": "Partial. Whole ward except for precincts 1, 4, 9, and 21.",
        "block_limits": True,
        "homeowner_req": True,
        "admin_adj": True,
    },
    31: {
        "type": "full",
        "block_limits": False,
        "homeowner_req": False,
        "admin_adj": False,
    },
    32: {
        "type": "full",
        "block_limits": True,
        "homeowner_req": True,
        "admin_adj": True,
    },
    33: {
        "type": "full",
        "block_limits": False,
        "homeowner_req": False,
        "admin_adj": False,
    },
    34: {
        "type": "full",
        "block_limits": False,
        "homeowner_req": False,
        "admin_adj": False,
    },
    35: {
        "type": "full",
        "block_limits": False,
        "homeowner_req": False,
        "admin_adj": False,
    },
    36: {
        "type": "full",
        "block_limits": False,
        "homeowner_req": False,
        "admin_adj": False,
    },
    40: {
        "type": "full",
        "block_limits": False,
        "homeowner_req": False,
        "admin_adj": False,
    },
    42: {
        "type": "not_eligible",
        "block_limits": False,
        "homeowner_req": False,
        "admin_adj": False,
        "notes": "not eligible (no SFH zoning to opt-in)",
    },
    43: {
        "type": "full",
        "block_limits": False,
        "homeowner_req": False,
        "admin_adj": False,
    },
    44: {
        "type": "full",
        "block_limits": False,
        "homeowner_req": False,
        "admin_adj": False,
    },
    46: {
        "type": "full",
        "block_limits": False,
        "homeowner_req": False,
        "admin_adj": False,
    },
    47: {
        "type": "full",
        "block_limits": False,
        "homeowner_req": False,
        "admin_adj": False,
    },
    48: {
        "type": "full",
        "block_limits": False,
        "homeowner_req": False,
        "admin_adj": False,
    },
    49: {
        "type": "full",
        "block_limits": False,
        "homeowner_req": False,
        "admin_adj": False,
    },
}

PROJECT_TITLE = "ADU Opt-In Dashboard"
PROJECT_DESCRIPTION = (
    "The City Council’s September 2025 ADU ordinance re-legalized accessory dwelling units (coach houses, basement apartments, granny flats), "
    "but each alderperson must opt in their ward.\n\n"
    "This dashboard tracks opt-ins and gives you tools to contact your alderperson if your ward hasn’t opted in yet.\n\n"
    "For more on how this change came about, see the "
    "[Strong Towns ADU legalization win page](https://www.strongtownschicago.org/milestones/adu-legalization-win) "
    "or the [Abundant Housing Illinois ADU FAQ](https://abundanthousingillinois.org/resources/accessory-dwelling-units-faq/)."
)
PROJECT_LINK = "https://www.strongtownschicago.org/milestones/adu-legalization-win"

GROUP_CONFIG = [
    {
        "name": "Strong Towns Chicago",
        "description": "Empowers neighborhoods to incrementally build a more financially resilient city.",
        "slug": "adu-opt-in-dashboard",
    },
    {
        "name": "Abundant Housing Illinois",
        "description": "Advocates for more homes in more places across Illinois.",
        "slug": "ahil-adu-opt-in-dashboard",
    },
]


def format_restriction_notes(info):
    restrictions = []
    if info["block_limits"]:
        restrictions.append("Block limits apply")
    if info["homeowner_req"]:
        restrictions.append("Homeowner requirement applies")
    if info["admin_adj"]:
        restrictions.append("Administrative adjustment applies")
    return "; ".join(restrictions)


async def import_adu_project_data():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("adu-opt-in-import")

    jurisdiction_service = get_cached_jurisdiction_service()
    entity_service = get_cached_entity_service()
    project_service = get_cached_project_service()
    group_service = get_cached_group_service()
    status_service = get_cached_status_service()

    jurisdiction = await jurisdiction_service.find_by_name("Chicago City Council")
    if not jurisdiction:
        logger.error("Chicago City Council jurisdiction not found.")
        return

    entities = await entity_service.list_entities(jurisdiction_id=jurisdiction.id)
    logger.info(f"Found {len(entities)} alderpersons.")

    for group_cfg in GROUP_CONFIG:
        group = await group_service.find_or_create_by_name(
            group_cfg["name"],
            group_cfg["description"],
        )
        slug = group_cfg["slug"]

        # Idempotency: skip if project already exists
        existing_project = await project_service.get_project_by_slug(slug)
        if existing_project:
            logger.info(f"Project '{slug}' already exists, skipping.")
            continue

        project = await project_service.create_project(
            ProjectBase(
                title=PROJECT_TITLE,
                description=PROJECT_DESCRIPTION,
                status=ProjectStatus.ACTIVE,
                active=True,
                link=PROJECT_LINK,
                preferred_status=EntityStatus.SOLID_APPROVAL,
                jurisdiction_id=jurisdiction.id,
                group_id=group.id,
                created_by="admin",
                slug=slug,
                dashboard_config=DashboardConfig(
                    representative_title="Alderperson",
                    status_labels={
                        "solid_approval": "Fully Opted In",
                        "leaning_approval": "Partially Opted In",
                        "neutral": "Not Eligible",
                        "leaning_disapproval": "Not Opted In",
                        "solid_disapproval": "Strongly Opposed",
                        "unknown": "Unknown",
                    },
                    metrics=[
                        MetricDisplayConfig(
                            key="rs_zoned_pct",
                            label="RS-Zoned Land",
                            description="Percentage of land in this ward zoned RS (Residential Single-Unit). RS zoning restricts land to single-family homes and affects how many properties are eligible for ADU construction. Data sourced from the Chicago Cityscape Zoning Explorer API.",
                            format="percentage",
                            show_in_table=True,
                            show_in_tooltip=True,
                        )
                    ],
                ),
            )
        )
        logger.info(
            f"Created project: {project.title} (slug: {slug}, group: {group.name})"
        )

        for entity in entities:
            ward_number = None
            if hasattr(entity, "district_name") and entity.district_name:
                if entity.district_name.lower().startswith("ward "):
                    try:
                        ward_number = int(entity.district_name.split(" ")[1])
                    except Exception:
                        pass
            elif hasattr(entity, "district_code") and entity.district_code:
                try:
                    ward_number = int(entity.district_code)
                except Exception:
                    pass

            info = (
                WARD_OPT_IN_INFO.get(ward_number) if ward_number is not None else None
            )
            notes: str | None = None
            status: EntityStatus = EntityStatus.UNKNOWN
            if info:
                if info["type"] == "not_eligible":
                    status = EntityStatus.NEUTRAL
                elif info["type"] == "full":
                    status = EntityStatus.SOLID_APPROVAL
                elif info["type"] == "partial":
                    status = EntityStatus.LEANING_APPROVAL
                if "notes" in info:
                    notes = str(info["notes"])
                    restriction_notes = format_restriction_notes(info)
                    if restriction_notes:
                        notes = f"{notes}. Restrictions: {restriction_notes}"
            else:
                status = EntityStatus.LEANING_DISAPPROVAL

            record_metadata: dict[str, float] | None = None
            if ward_number is not None and ward_number in WARD_RS_ZONED_PCT:
                record_metadata = {"rs_zoned_pct": WARD_RS_ZONED_PCT[ward_number]}

            status_record = EntityStatusRecord(
                entity_id=entity.id,
                project_id=project.id,
                status=status,
                notes=notes,
                record_metadata=record_metadata,
                updated_by="admin",
            )
            await status_service.create_status_record(status_record)
            logger.info(
                f"Set status for {entity.name} (Ward {ward_number}): {status} | {notes}"
            )

    logger.info("ADU Opt-In project import completed.")


if __name__ == "__main__":
    asyncio.run(import_adu_project_data())
