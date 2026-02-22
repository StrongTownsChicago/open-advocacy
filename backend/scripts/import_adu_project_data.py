import asyncio
import logging
from app.services.service_factory import (
    get_cached_jurisdiction_service,
    get_cached_entity_service,
    get_cached_project_service,
    get_cached_group_service,
    get_cached_status_service,
)
from app.models.pydantic.models import ProjectBase, EntityStatusRecord, EntityStatus

WARD_OPT_IN_INFO = {
    1:  {"type": "full", "block_limits": False, "homeowner_req": False, "admin_adj": False},
    3:  {"type": "not_eligible", "block_limits": False, "homeowner_req": False, "admin_adj": False, "notes": "not eligible (no SFH zoning to opt-in)"},
    4:  {"type": "full", "block_limits": False, "homeowner_req": False, "admin_adj": False},
    5:  {"type": "full", "block_limits": False, "homeowner_req": False, "admin_adj": False},
    6:  {"type": "full", "notes": "Whole ward (including the part currently in the pilot)", "block_limits": True, "homeowner_req": True, "admin_adj": True},
    12: {"type": "full", "block_limits": False, "homeowner_req": False, "admin_adj": False},
    14: {"type": "partial", "notes": "Partial. Only precincts 1, 4, 9, and 15", "block_limits": True, "homeowner_req": True, "admin_adj": True},
    22: {"type": "full", "block_limits": True, "homeowner_req": True, "admin_adj": True},
    25: {"type": "full", "block_limits": True, "homeowner_req": True, "admin_adj": True},
    26: {"type": "full", "block_limits": False, "homeowner_req": False, "admin_adj": False},
    27: {"type": "full", "block_limits": False, "homeowner_req": False, "admin_adj": False},
    29: {"type": "full", "block_limits": False, "homeowner_req": False, "admin_adj": False},
    30: {"type": "partial", "notes": "Partial. Whole ward except for precincts 1, 4, 9, and 21.", "block_limits": True, "homeowner_req": True, "admin_adj": True},
    31: {"type": "full", "block_limits": False, "homeowner_req": False, "admin_adj": False},
    32: {"type": "full", "block_limits": True, "homeowner_req": True, "admin_adj": True},
    33: {"type": "full", "block_limits": False, "homeowner_req": False, "admin_adj": False},
    34: {"type": "full", "block_limits": False, "homeowner_req": False, "admin_adj": False},
    35: {"type": "full", "block_limits": False, "homeowner_req": False, "admin_adj": False},
    36: {"type": "full", "block_limits": False, "homeowner_req": False, "admin_adj": False},
    40: {"type": "full", "block_limits": False, "homeowner_req": False, "admin_adj": False},
    42: {"type": "not_eligible", "block_limits": False, "homeowner_req": False, "admin_adj": False, "notes": "not eligible (no SFH zoning to opt-in)"},
    43: {"type": "full", "block_limits": False, "homeowner_req": False, "admin_adj": False},
    44: {"type": "full", "block_limits": False, "homeowner_req": False, "admin_adj": False},
    46: {"type": "full", "block_limits": False, "homeowner_req": False, "admin_adj": False},
    47: {"type": "full", "block_limits": False, "homeowner_req": False, "admin_adj": False},
    48: {"type": "full", "block_limits": False, "homeowner_req": False, "admin_adj": False},
    49: {"type": "full", "block_limits": False, "homeowner_req": False, "admin_adj": False},
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

    group = await group_service.find_or_create_by_name(
        "Strong Towns Chicago",
        "Empowers neighborhoods to incrementally build a more financially resilient city.",
    )

    project = await project_service.create_project(
        ProjectBase(
            title=PROJECT_TITLE,
            description=PROJECT_DESCRIPTION,
            status="active",
            active=True,
            link=PROJECT_LINK,
            preferred_status=EntityStatus.SOLID_APPROVAL,
            jurisdiction_id=jurisdiction.id,
            group_id=group.id,
            created_by="admin",
        )
    )
    logger.info(f"Created project: {project.title}")

    entities = await entity_service.list_entities(jurisdiction_id=jurisdiction.id)
    logger.info(f"Found {len(entities)} alderpersons.")

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

        info = WARD_OPT_IN_INFO.get(ward_number)
        notes = None
        status = None
        if info:
            if info["type"] == "not_eligible":
                status = EntityStatus.NEUTRAL
            elif info["type"] == "full":
                status = EntityStatus.SOLID_APPROVAL
            elif info["type"] == "partial":
                status = EntityStatus.LEANING_APPROVAL
            if "notes" in info:
                notes = info["notes"]
                restriction_notes = format_restriction_notes(info)
                if restriction_notes:
                    notes = f"{notes}. Restrictions: {restriction_notes}"
        else:
            status = EntityStatus.LEANING_DISAPPROVAL

        status_record = EntityStatusRecord(
            entity_id=entity.id,
            project_id=project.id,
            status=status,
            notes=notes,
            updated_by="admin",
        )
        await status_service.create_status_record(status_record)
        logger.info(f"Set status for {entity.name} (Ward {ward_number}): {status} | {notes}")

    logger.info("ADU Opt-In project import completed.")

if __name__ == "__main__":
    asyncio.run(import_adu_project_data())