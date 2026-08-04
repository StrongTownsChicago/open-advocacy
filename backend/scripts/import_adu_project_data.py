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
        "name": "Strong Towns Chicago — Chicago City Council",
        "description": "Empowers neighborhoods to incrementally build a more financially resilient city.",
        "slug": "adu-opt-in-dashboard",
    },
    {
        "name": "Abundant Housing Illinois — Chicago City Council",
        "description": "Advocates for more homes in more places across Illinois.",
        "slug": "ahil-adu-opt-in-dashboard",
    },
]


RESTRICTION_LABELS = [
    ("block_limits", "Block cap", "Annual block cap applies"),
    ("homeowner_req", "Owner occupancy", "Owner-occupancy requirement applies"),
    ("admin_adj", "Admin adjustment", "Administrative adjustment required"),
]

# The dashboard conveys two independent axes -- how much of the ward opted in,
# and whether limitations apply -- through the single status field that drives
# the map colour. EntityStatus is used here as a six-point ordinal scale, with
# the per-project labels and colours below.
STATUS_LABELS = {
    "solid_approval": "Whole ward — no added restrictions",
    "leaning_approval": "Whole ward — with restrictions",
    "neutral": "Part of ward — no added restrictions",
    "leaning_disapproval": "Part of ward — with restrictions",
    "solid_disapproval": "Not opted in",
    "unknown": "Not eligible (no RS zoning)",
}

# The default palette reserves grey for "not applicable", leaving only four
# ordinal colours. Crossing the two axes needs five, so this project supplies
# its own ramp: green -> lime -> amber -> orange -> red, plus grey.
STATUS_COLORS = {
    "solid_approval": "#166534",
    "leaning_approval": "#65a30d",
    "neutral": "#eab308",
    "leaning_disapproval": "#f97316",
    "solid_disapproval": "#dc2626",
    "unknown": "#94a3b8",
}


def format_restriction_notes(info):
    return "; ".join(
        sentence for key, _short, sentence in RESTRICTION_LABELS if info[key]
    )


def summarize_restrictions(info):
    """Compact restrictions value for the table column and map tooltip."""
    if info is None or info["type"] == "not_eligible":
        return "—"
    short = [short for key, short, _ in RESTRICTION_LABELS if info[key]]
    return ", ".join(short) if short else "None"


def resolve_status(info):
    """Cross ward extent with restrictions to get one ordinal status."""
    if info is None:
        return EntityStatus.SOLID_DISAPPROVAL
    if info["type"] == "not_eligible":
        return EntityStatus.UNKNOWN
    restricted = any(info[key] for key, _, _ in RESTRICTION_LABELS)
    if info["type"] == "full":
        return (
            EntityStatus.LEANING_APPROVAL if restricted else EntityStatus.SOLID_APPROVAL
        )
    return EntityStatus.LEANING_DISAPPROVAL if restricted else EntityStatus.NEUTRAL


def build_notes(info):
    """Status note. Restrictions are always stated, with or without a note."""
    if info is None:
        return None
    parts = []
    if "notes" in info:
        parts.append(str(info["notes"]).rstrip("."))
    restrictions = format_restriction_notes(info)
    if restrictions:
        parts.append(f"Restrictions: {restrictions}")
    elif info["type"] in ("full", "partial"):
        parts.append("No added restrictions apply")
    return ". ".join(parts) + "." if parts else None


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
                    status_labels=STATUS_LABELS,
                    status_colors=STATUS_COLORS,
                    metrics=[
                        MetricDisplayConfig(
                            key="restrictions",
                            label="Restrictions",
                            description="Limitations the alderperson attached to their opt-in. Annual block cap limits how many ADU permits can be issued per block per year; owner occupancy requires the owner to live on the property; administrative adjustment requires Zoning Administrator approval and a fee.",
                            format="text",
                            show_in_table=True,
                            show_in_tooltip=True,
                        ),
                        MetricDisplayConfig(
                            key="rs_zoned_pct",
                            label="RS-Zoned Land",
                            description="Percentage of land in this ward zoned RS (Residential Single-Unit). RS zoning restricts land to single-family homes and affects how many properties are eligible for ADU construction. Data sourced from the Chicago Cityscape Zoning Explorer API.",
                            format="percentage",
                            show_in_table=True,
                            show_in_tooltip=False,
                        ),
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
            status = resolve_status(info)
            notes = build_notes(info)

            record_metadata: dict[str, object] = {
                "restrictions": summarize_restrictions(info)
            }
            if ward_number is not None and ward_number in WARD_RS_ZONED_PCT:
                record_metadata["rs_zoned_pct"] = WARD_RS_ZONED_PCT[ward_number]

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
