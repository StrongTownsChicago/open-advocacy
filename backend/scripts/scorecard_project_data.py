"""Scorecard project and group configuration data.

All project definitions and group config for the scorecard import script.
Used by both import_scorecard_projects.py and scorecard_refresh_service.
"""

from typing import Any

from app.models.pydantic.models import EntityStatus

# ---------------------------------------------------------------------------
# Chicago project definitions (ELMS data source)
# ---------------------------------------------------------------------------

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

# Abundant Housing Illinois: all Chicago projects
AHIL_BASE_SLUGS = {p["base_slug"] for p in ALL_SCORECARD_PROJECTS}

# ---------------------------------------------------------------------------
# IL General Assembly project definitions (OpenStates data source)
# ---------------------------------------------------------------------------

_IL_SPONSORSHIP_LABELS: dict[str, str] = {
    "solid_approval": "Cosponsored",
    "neutral": "Not a Cosponsor",
    "unknown": "Not in Office",
}

_IL_VOTE_LABELS: dict[str, str] = {
    "solid_approval": "Voted Yes",
    "solid_disapproval": "Voted No",
    "neutral": "Absent/Not Voting",
    "unknown": "Not in Office",
}

_IL_COMMITTEE_VOTE_LABELS: dict[str, str] = {
    "solid_approval": "Voted Yes",
    "solid_disapproval": "Voted No",
    "neutral": "Absent/Not Voting",
    "unknown": "Not on Committee",
}

ALL_IL_SCORECARD_PROJECTS: list[dict[str, Any]] = [
    # --- IL Senate bills ---
    {
        "base_slug": "il-build-act-sb4060-sponsorship",
        "title": "Build Act — Middle Housing (SB 4060) — Cosponsors",
        "description": (
            "Would allow middle housing types (duplexes, triplexes, etc.) in municipalities "
            "across Illinois, reducing exclusionary zoning. Currently in committee. "
            "Source: https://www.ilga.gov/legislation/BillStatus.asp?DocNum=4060&GAID=18&DocTypeID=SB"
        ),
        "bill_identifier": "SB 4060",
        "chamber": "senate",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": _IL_SPONSORSHIP_LABELS,
    },
    {
        "base_slug": "il-single-stair-sb4061-sponsorship",
        "title": "Single Stair Act (SB 4061) — Cosponsors",
        "description": (
            "Would allow new residential buildings up to 6 stories to use a single exit "
            "stairwell (paired with a fire-rated elevator), reducing construction costs and "
            "enabling more efficient floor plans for small-to-mid-rise apartments statewide. "
            "Currently in committee. "
            "Source: https://www.ilga.gov/legislation/BillStatus.asp?DocNum=4061&GAID=18&DocTypeID=SB"
        ),
        "bill_identifier": "SB 4061",
        "chamber": "senate",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": _IL_SPONSORSHIP_LABELS,
    },
    {
        "base_slug": "il-build-act-sb4062-sponsorship",
        "title": "Build Act — Impact Fees (SB 4062) — Cosponsors",
        "description": (
            "Would reform impact mitigation fees charged to new housing development, "
            "reducing upfront costs that limit housing production. Currently in committee. "
            "Source: https://www.ilga.gov/legislation/BillStatus.asp?DocNum=4062&GAID=18&DocTypeID=SB"
        ),
        "bill_identifier": "SB 4062",
        "chamber": "senate",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": _IL_SPONSORSHIP_LABELS,
    },
    {
        "base_slug": "il-build-act-sb4063-sponsorship",
        "title": "Build Act — Building Plans (SB 4063) — Cosponsors",
        "description": (
            "Would streamline municipal review of residential building plans and inspections, "
            "reducing delays in the housing permitting process. Currently in committee. "
            "Source: https://www.ilga.gov/legislation/BillStatus.asp?DocNum=4063&GAID=18&DocTypeID=SB"
        ),
        "bill_identifier": "SB 4063",
        "chamber": "senate",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": _IL_SPONSORSHIP_LABELS,
    },
    {
        "base_slug": "il-build-act-sb4064-sponsorship",
        "title": "Build Act — Residential Parking (SB 4064) — Cosponsors",
        "description": (
            "Would allow municipalities to reduce or eliminate residential parking minimums "
            "near transit, lowering the cost of housing development. Currently in committee. "
            "Source: https://www.ilga.gov/legislation/BillStatus.asp?DocNum=4064&GAID=18&DocTypeID=SB"
        ),
        "bill_identifier": "SB 4064",
        "chamber": "senate",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": _IL_SPONSORSHIP_LABELS,
    },
    {
        "base_slug": "il-build-act-sb4071-sponsorship",
        "title": "Build Act — ADUs (SB 4071) — Cosponsors",
        "description": (
            "Would legalize accessory dwelling units (ADUs) — coach houses, basement "
            "apartments, backyard cottages — statewide, enabling more housing on existing "
            "residential lots. Currently in committee. "
            "Source: https://www.ilga.gov/legislation/BillStatus.asp?DocNum=4071&GAID=18&DocTypeID=SB"
        ),
        "bill_identifier": "SB 4071",
        "chamber": "senate",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": _IL_SPONSORSHIP_LABELS,
    },
    {
        "base_slug": "il-yigby-sb3187-sponsorship",
        "title": "YIGBY / Church Land Act (SB 3187) — Cosponsors",
        "description": (
            "Would allow religious institutions to develop affordable housing on their "
            "land (Yes In God's Backyard), unlocking underutilized faith community sites "
            "for housing production. Currently in committee. "
            "Source: https://www.ilga.gov/legislation/BillStatus.asp?DocNum=3187&GAID=18&DocTypeID=SB"
        ),
        "bill_identifier": "SB 3187",
        "chamber": "senate",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": _IL_SPONSORSHIP_LABELS,
    },
    {
        "base_slug": "il-sb3169-sponsorship",
        "title": "Affordable Housing Revenue (SB 3169) — Cosponsors",
        "description": (
            "Would create new revenue mechanisms to fund affordable housing construction "
            "and preservation across Illinois. Currently in committee. "
            "Source: https://www.ilga.gov/legislation/BillStatus.asp?DocNum=3169&GAID=18&DocTypeID=SB"
        ),
        "bill_identifier": "SB 3169",
        "chamber": "senate",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": _IL_SPONSORSHIP_LABELS,
    },
    {
        "base_slug": "il-sb3212-sponsorship",
        "title": "Transit Opportunity Zone Act (SB 3212) — Cosponsors",
        "description": (
            "Would establish Transit Opportunity Zones to incentivize affordable housing "
            "development near public transit. Currently in committee. "
            "Source: https://www.ilga.gov/legislation/BillStatus.asp?DocNum=3212&GAID=18&DocTypeID=SB"
        ),
        "bill_identifier": "SB 3212",
        "chamber": "senate",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": _IL_SPONSORSHIP_LABELS,
    },
    {
        "base_slug": "il-sb3738-sponsorship",
        "title": "Affordable Housing Revenue (SB 3738) — Cosponsors",
        "description": (
            "Would provide additional revenue sources for affordable housing programs "
            "across Illinois. Currently in committee. "
            "Source: https://www.ilga.gov/legislation/BillStatus.asp?DocNum=3738&GAID=18&DocTypeID=SB"
        ),
        "bill_identifier": "SB 3738",
        "chamber": "senate",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": _IL_SPONSORSHIP_LABELS,
    },
    {
        "base_slug": "il-sb4162-sponsorship",
        "title": "Home for Good Act (SB 4162) — Cosponsors",
        "description": (
            "Would strengthen tenant protections and provide resources for households "
            "at risk of homelessness. Currently in committee. "
            "Source: https://www.ilga.gov/legislation/BillStatus.asp?DocNum=4162&GAID=18&DocTypeID=SB"
        ),
        "bill_identifier": "SB 4162",
        "chamber": "senate",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": _IL_SPONSORSHIP_LABELS,
    },
    {
        "base_slug": "il-transit-funding-sb2111-sponsorship",
        "title": "Northern Illinois Transit Authority Act (SB 2111) — Cosponsors",
        "description": (
            "Shell bill repurposed for transit funding for the Northern Illinois region. "
            "Passed both chambers and signed into law as Public Act 104-0457. "
            "Source: https://www.ilga.gov/legislation/BillStatus.asp?DocNum=2111&GAID=18&DocTypeID=SB"
        ),
        "bill_identifier": "SB 2111",
        "chamber": "senate",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": _IL_SPONSORSHIP_LABELS,
        "position": 2,
    },
    {
        "base_slug": "il-transit-funding-sb2111-vote",
        "title": "Northern Illinois Transit Authority Act (SB 2111) — Senate Vote",
        "description": (
            "Senate floor vote on SB 2111 transit funding bill. "
            "Passed the Senate 47-4 and signed into law as Public Act 104-0457. "
            "Source: https://www.ilga.gov/legislation/BillStatus.asp?DocNum=2111&GAID=18&DocTypeID=SB"
        ),
        "bill_identifier": "SB 2111",
        "chamber": "senate",
        "import_type": "vote",
        "vote_date": "2025-04-10",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": _IL_VOTE_LABELS,
        "position": 1,
    },
    {
        "base_slug": "il-transit-funding-sb2111-house-vote",
        "title": "Northern Illinois Transit Authority Act (SB 2111) — House Vote",
        "description": (
            "House floor vote on SB 2111 transit funding bill. "
            "Passed the House 72-32 on 10/31/2025 and signed into law as Public Act 104-0457. "
            "Source: https://www.ilga.gov/legislation/BillStatus.asp?DocNum=2111&GAID=18&DocTypeID=SB"
        ),
        "bill_identifier": "SB 2111",
        "chamber": "house",
        "import_type": "vote",
        "vote_date": "2025-10-31",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": _IL_VOTE_LABELS,
        "position": 1,
    },
    {
        "base_slug": "il-transit-funding-sb2111-house-sponsorship",
        "title": "Northern Illinois Transit Authority Act (SB 2111) — House Cosponsors",
        "description": (
            "House members who cosponsored SB 2111 transit funding bill. "
            "Signed into law as Public Act 104-0457. "
            "Source: https://www.ilga.gov/legislation/BillStatus.asp?DocNum=2111&GAID=18&DocTypeID=SB"
        ),
        "bill_identifier": "SB 2111",
        "chamber": "house",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": _IL_SPONSORSHIP_LABELS,
        "position": 2,
    },
    # --- IL House bills ---
    {
        "base_slug": "il-build-act-hb5626-sponsorship",
        "title": "Build Act — ADUs (HB 5626) — Cosponsors",
        "description": (
            "House companion to SB 4071 — would legalize accessory dwelling units (ADUs) "
            "statewide. Currently in committee. "
            "Source: https://www.ilga.gov/legislation/BillStatus.asp?DocNum=5626&GAID=18&DocTypeID=HB"
        ),
        "bill_identifier": "HB 5626",
        "chamber": "house",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": _IL_SPONSORSHIP_LABELS,
    },
    {
        "base_slug": "il-yigby-hb5083-sponsorship",
        "title": "YIGBY / Church Land Act (HB 5083) — Cosponsors",
        "description": (
            "House companion to SB 3187 — would allow religious institutions to develop "
            "affordable housing on their land. Currently in committee. "
            "Source: https://www.ilga.gov/legislation/BillStatus.asp?DocNum=5083&GAID=18&DocTypeID=HB"
        ),
        "bill_identifier": "HB 5083",
        "chamber": "house",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": _IL_SPONSORSHIP_LABELS,
    },
    {
        "base_slug": "il-hb1813-sponsorship",
        "title": "ADU Reform (HB 1813) — Cosponsors",
        "description": (
            "Would reform accessory dwelling unit regulations statewide, enabling more "
            "homeowners to add ADUs to their properties. Currently in committee. "
            "Source: https://www.ilga.gov/legislation/BillStatus.asp?DocNum=1813&GAID=18&DocTypeID=HB"
        ),
        "bill_identifier": "HB 1813",
        "chamber": "house",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": _IL_SPONSORSHIP_LABELS,
    },
    {
        "base_slug": "il-hb1813-vote",
        "title": "ADU Reform (HB 1813) — Committee Vote",
        "description": (
            "House committee vote on HB 1813 ADU reform bill (18-0 on 2025-03-20). "
            "Source: https://www.ilga.gov/legislation/BillStatus.asp?DocNum=1813&GAID=18&DocTypeID=HB"
        ),
        "bill_identifier": "HB 1813",
        "chamber": "house",
        "import_type": "vote",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": _IL_COMMITTEE_VOTE_LABELS,
    },
    {
        "base_slug": "il-hb1814-sponsorship",
        "title": "Middle Housing Zoning (HB 1814) — Cosponsors",
        "description": (
            "Would require municipalities to allow middle housing types (duplexes, "
            "triplexes, etc.) in residential zones statewide. Currently in committee. "
            "Source: https://www.ilga.gov/legislation/BillStatus.asp?DocNum=1814&GAID=18&DocTypeID=HB"
        ),
        "bill_identifier": "HB 1814",
        "chamber": "house",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": _IL_SPONSORSHIP_LABELS,
    },
    {
        "base_slug": "il-hb1814-vote",
        "title": "Middle Housing Zoning (HB 1814) — Committee Vote",
        "description": (
            "House committee vote on HB 1814 middle housing zoning bill (12-6 on 2025-03-20). "
            "Source: https://www.ilga.gov/legislation/BillStatus.asp?DocNum=1814&GAID=18&DocTypeID=HB"
        ),
        "bill_identifier": "HB 1814",
        "chamber": "house",
        "import_type": "vote",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": _IL_COMMITTEE_VOTE_LABELS,
    },
    {
        "base_slug": "il-hb4283-sponsorship",
        "title": "First-Generation Homebuyer Loans (HB 4283) — Cosponsors",
        "description": (
            "Would create a loan program to assist first-generation homebuyers who lack "
            "family wealth to fund down payments. Currently in committee. "
            "Source: https://www.ilga.gov/legislation/BillStatus.asp?DocNum=4283&GAID=18&DocTypeID=HB"
        ),
        "bill_identifier": "HB 4283",
        "chamber": "house",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": _IL_SPONSORSHIP_LABELS,
    },
    {
        "base_slug": "il-hb4377-sponsorship",
        "title": "PHA — No Work Requirements (HB 4377) — Cosponsors",
        "description": (
            "Would prohibit public housing authorities from imposing work requirements "
            "as a condition of housing assistance. Currently in committee. "
            "Source: https://www.ilga.gov/legislation/BillStatus.asp?DocNum=4377&GAID=18&DocTypeID=HB"
        ),
        "bill_identifier": "HB 4377",
        "chamber": "house",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": _IL_SPONSORSHIP_LABELS,
    },
    {
        "base_slug": "il-hb4571-sponsorship",
        "title": "Affordable Housing Code Reform (HB 4571) — Cosponsors",
        "description": (
            "Would reform city codes to remove barriers to affordable housing construction "
            "and preservation. Currently in committee. "
            "Source: https://www.ilga.gov/legislation/BillStatus.asp?DocNum=4571&GAID=18&DocTypeID=HB"
        ),
        "bill_identifier": "HB 4571",
        "chamber": "house",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": _IL_SPONSORSHIP_LABELS,
    },
    {
        "base_slug": "il-hb4571-vote",
        "title": "Affordable Housing Code Reform (HB 4571) — Committee Vote",
        "description": (
            "House committee vote on HB 4571 affordable housing code reform bill (12-5 on 2026-02-18). "
            "Source: https://www.ilga.gov/legislation/BillStatus.asp?DocNum=4571&GAID=18&DocTypeID=HB"
        ),
        "bill_identifier": "HB 4571",
        "chamber": "house",
        "import_type": "vote",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": _IL_COMMITTEE_VOTE_LABELS,
    },
    {
        "base_slug": "il-hb4835-sponsorship",
        "title": "Adaptive Reuse (HB 4835) — Cosponsors",
        "description": (
            "Would facilitate the conversion of underutilized commercial and office "
            "buildings into residential units. Currently in committee. "
            "Source: https://www.ilga.gov/legislation/BillStatus.asp?DocNum=4835&GAID=18&DocTypeID=HB"
        ),
        "bill_identifier": "HB 4835",
        "chamber": "house",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": _IL_SPONSORSHIP_LABELS,
    },
    {
        "base_slug": "il-hb4841-sponsorship",
        "title": "Affordable Housing Tax Incentive (HB 4841) — Cosponsors",
        "description": (
            "Would create income tax incentives for affordable housing development "
            "and preservation. Currently in committee. "
            "Source: https://www.ilga.gov/legislation/BillStatus.asp?DocNum=4841&GAID=18&DocTypeID=HB"
        ),
        "bill_identifier": "HB 4841",
        "chamber": "house",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": _IL_SPONSORSHIP_LABELS,
    },
    {
        "base_slug": "il-hb4998-sponsorship",
        "title": "Statewide Tenant Protections (HB 4998) — Cosponsors",
        "description": (
            "Would establish baseline tenant protections across Illinois, including "
            "just-cause eviction requirements. Currently in committee. "
            "Source: https://www.ilga.gov/legislation/BillStatus.asp?DocNum=4998&GAID=18&DocTypeID=HB"
        ),
        "bill_identifier": "HB 4998",
        "chamber": "house",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": _IL_SPONSORSHIP_LABELS,
    },
    {
        "base_slug": "il-hb5198-sponsorship",
        "title": "Affordable Housing CILAs (HB 5198) — Cosponsors",
        "description": (
            "Would expand affordable housing options for people with disabilities "
            "through Community Integrated Living Arrangements (CILAs). Currently in committee. "
            "Source: https://www.ilga.gov/legislation/BillStatus.asp?DocNum=5198&GAID=18&DocTypeID=HB"
        ),
        "bill_identifier": "HB 5198",
        "chamber": "house",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": _IL_SPONSORSHIP_LABELS,
    },
    {
        "base_slug": "il-hb5394-sponsorship",
        "title": "Credit Score Protections (HB 5394) — Cosponsors",
        "description": (
            "Would prohibit landlords from using credit scores as the sole basis for "
            "denying rental applications, expanding housing access. Currently in committee. "
            "Source: https://www.ilga.gov/legislation/BillStatus.asp?DocNum=5394&GAID=18&DocTypeID=HB"
        ),
        "bill_identifier": "HB 5394",
        "chamber": "house",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": _IL_SPONSORSHIP_LABELS,
    },
    {
        "base_slug": "il-hb5616-sponsorship",
        "title": "Anti-Growth Law Preemption (HB 5616) — Cosponsors",
        "description": (
            "Would preempt local anti-growth ordinances that restrict new housing "
            "development, removing barriers to housing production statewide. Currently in committee. "
            "Source: https://www.ilga.gov/legislation/BillStatus.asp?DocNum=5616&GAID=18&DocTypeID=HB"
        ),
        "bill_identifier": "HB 5616",
        "chamber": "house",
        "import_type": "sponsorship",
        "preferred_status": EntityStatus.SOLID_APPROVAL,
        "status_labels": _IL_SPONSORSHIP_LABELS,
    },
]

# IL Senate bill base slugs
IL_SENATE_BASE_SLUGS: set[str] = {
    p["base_slug"] for p in ALL_IL_SCORECARD_PROJECTS if p["chamber"] == "senate"
}

# IL House bill base slugs
IL_HOUSE_BASE_SLUGS: set[str] = {
    p["base_slug"] for p in ALL_IL_SCORECARD_PROJECTS if p["chamber"] == "house"
}

# ---------------------------------------------------------------------------
# Group configuration
# ---------------------------------------------------------------------------

GROUP_CONFIG: list[dict[str, Any]] = [
    {
        "name": "Strong Towns Chicago",
        "description": "Empowers neighborhoods to incrementally build a more financially resilient city.",
        "jurisdiction_name": "Chicago City Council",
        "base_slugs": STC_BASE_SLUGS,
        "slug_prefix": "",
        "data_source": "elms",
        "representative_title": "Alderperson",
    },
    {
        "name": "Abundant Housing Illinois — Chicago City Council",
        "description": "Advocates for more homes in more places across Illinois.",
        "jurisdiction_name": "Chicago City Council",
        "base_slugs": AHIL_BASE_SLUGS,
        "slug_prefix": "ahil-",
        "data_source": "elms",
        "representative_title": "Alderperson",
    },
    {
        "name": "Abundant Housing Illinois — IL House",
        "description": "Advocates for more homes in more places across Illinois.",
        "jurisdiction_name": "Illinois House of Representatives",
        "base_slugs": IL_HOUSE_BASE_SLUGS,
        "slug_prefix": "ahil-house-",
        "data_source": "il_openstates",
        "representative_title": "Representative",
    },
    {
        "name": "Abundant Housing Illinois — IL Senate",
        "description": "Advocates for more homes in more places across Illinois.",
        "jurisdiction_name": "Illinois State Senate",
        "base_slugs": IL_SENATE_BASE_SLUGS,
        "slug_prefix": "ahil-senate-",
        "data_source": "il_openstates",
        "representative_title": "Senator",
    },
]
