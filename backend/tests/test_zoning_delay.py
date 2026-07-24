"""Tests for app.imports.sources.zoning_delay."""

from datetime import date

import pytest
from shapely.geometry import Polygon

from app.imports.sources.zoning_delay import (
    assign_ward,
    compute_ward_delay_stats,
    extract_address_from_title,
    is_alder_sponsored,
    load_ward_polygons,
    matched_alder_sponsors,
    meters_to_ward_boundary,
    unmatched_sponsor_names,
)

# ---------------------------------------------------------------------------
# extract_address_from_title
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "title,expected",
    [
        (
            "Zoning Reclassification Map No. 11-J at 4634-4636 N Avers Ave - App No. 23124T1",
            "4634 N Avers Ave",
        ),
        (
            "Zoning Reclassification Map No. 12-K at 5345-5353 S Archer Ave",
            "5345 S Archer Ave",
        ),
        # Missing space after "at"
        (
            "Zoning Reclassification Map No. 18-D at7200 S Dorchester Ave - App No. 23145",
            "7200 S Dorchester Ave",
        ),
        # Hyphen glued to the marker
        (
            "Zoning Reclassification Map No. 16-C-at 1834-2126 E 71st St, 1853-2007 E 71st St",
            "1834 E 71st St",
        ),
        # Hyphen glued to the App No. suffix
        (
            "Zoning Reclassification Map No. 1-G at 1133 W Kinzie St- App No. 23122",
            "1133 W Kinzie St",
        ),
        # Multi-address with "and"
        (
            "Zoning Reclassification Map No. 1-G at 370 N Morgan St, 400 N Morgan St "
            "and 403 N Carpenter St - App No. 23100",
            "370 N Morgan St",
        ),
        # Doubled space after "Map No."
        (
            "Zoning Reclassification Map No.  4-E at 1608 S Wabash Ave - App No. 23131",
            "1608 S Wabash Ave",
        ),
        # Space inside the house-number range
        (
            "Zoning Reclassification Map No. 16-C at 7108- 7116 S Euclid Ave",
            "7108 S Euclid Ave",
        ),
    ],
)
def test_extract_address_variants(title, expected):
    assert extract_address_from_title(title) == expected


@pytest.mark.parametrize(
    "title",
    [
        None,
        "",
        "Zoning Reclassification Map No. 1-G",
        "Zoning Reclassification Map No. 1-G at the intersection of Halsted and Clark",
        "Amendment of Municipal Code Title 17 regarding transit-oriented development",
    ],
)
def test_extract_address_returns_none_when_unparseable(title):
    assert extract_address_from_title(title) is None


def test_extract_address_rejects_bare_house_number():
    assert (
        extract_address_from_title("Zoning Reclassification Map No. 1-G at 1234")
        is None
    )


# ---------------------------------------------------------------------------
# assign_ward / load_ward_polygons
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_wards():
    return {
        1: Polygon([(0, 0), (0, 1), (1, 1), (1, 0)]),
        2: Polygon([(1, 0), (1, 1), (2, 1), (2, 0)]),
    }


def test_assign_ward_inside_polygon(fake_wards):
    # assign_ward takes (lat, lon) but polygons are (x=lon, y=lat)
    assert assign_ward(0.5, 0.5, fake_wards) == 1
    assert assign_ward(0.5, 1.5, fake_wards) == 2


def test_assign_ward_outside_all_polygons(fake_wards):
    assert assign_ward(5.0, 5.0, fake_wards) is None


def test_meters_to_ward_boundary_center_vs_edge():
    # ~1km square around Chicago's latitude: 0.009 deg lat ≈ 1000 m.
    lat0, lon0 = 41.9, -87.7
    d = 0.0045  # ~500 m half-width in latitude
    poly = Polygon(
        [
            (lon0 - d, lat0 - d),
            (lon0 - d, lat0 + d),
            (lon0 + d, lat0 + d),
            (lon0 + d, lat0 - d),
        ]
    )
    wards = {1: poly}
    # From the center, the nearest edge is a longitude edge: 0.0045 deg of
    # longitude at lat 41.9 ≈ 0.0045 * 111320 * cos(41.9°) ≈ 373 m (shorter
    # than the 501 m latitude edges because longitude is compressed by cos lat).
    center = meters_to_ward_boundary(lat0, lon0, wards, 1)
    assert center is not None and 355 < center < 390
    # A point very close to the top (latitude) edge is within a few meters.
    near_edge = meters_to_ward_boundary(lat0 + d - 0.00002, lon0, wards, 1)
    assert near_edge is not None and near_edge < 5


def test_meters_to_ward_boundary_unknown_ward():
    assert meters_to_ward_boundary(41.9, -87.7, {1: Polygon()}, 99) is None


def test_assign_ward_with_missing_coordinates(fake_wards):
    assert assign_ward(None, 0.5, fake_wards) is None
    assert assign_ward(0.5, None, fake_wards) is None
    assert assign_ward(None, None, fake_wards) is None


def test_load_ward_polygons_reads_all_50_chicago_wards():
    polygons = load_ward_polygons()
    assert len(polygons) == 50
    assert set(polygons) == set(range(1, 51))


@pytest.mark.parametrize(
    "lat,lon,ward",
    [
        # Interior points verified against Chicago's official post-2023 ward
        # boundaries dataset (data.cityofchicago.org, p293-wvbd, edit_date
        # 2022-06-01 = the remap effective with the 2023 election).
        (41.8837, -87.6319, 42),  # City Hall, 121 N LaSalle
        (41.9235, -87.6975, 1),  # 2354 N Milwaukee Ave (Ward 1)
        (41.9475, -87.6564, 44),  # 1060 W Addison St (Wrigley Field)
        (41.7794, -87.6446, 20),  # 63rd & Halsted
        (41.7217, -87.5385, 10),  # 9500 S Ewing Ave
    ],
)
def test_chicago_ward_polygons_match_post_2023_official_map(lat, lon, ward):
    """The committed geojson is the post-2023 remap; verify interior points.

    These points sit well inside their wards, so the committed polygons'
    simplification cannot flip the result (unlike near-boundary addresses).
    """
    polygons = load_ward_polygons()
    assert assign_ward(lat, lon, polygons) == ward


# ---------------------------------------------------------------------------
# compute_ward_delay_stats
# ---------------------------------------------------------------------------

AS_OF = date(2026, 1, 1)


def _matter(ward, intro, final=None, status="90-Final"):
    return {
        "ward": ward,
        "introductionDate": intro,
        "finalActionDate": final,
        "status": status,
    }


def test_median_over_resolved_matters():
    matters = [
        _matter(1, "2024-01-01T00:00:00+00:00", "2024-01-11T00:00:00+00:00"),
        _matter(1, "2024-01-01T00:00:00+00:00", "2024-01-21T00:00:00+00:00"),
        _matter(1, "2024-01-01T00:00:00+00:00", "2024-02-01T00:00:00+00:00"),
    ]
    stats = compute_ward_delay_stats(matters, AS_OF)
    assert stats[1]["zoning_median_days"] == 20.0
    assert stats[1]["n_resolved"] == 3
    assert stats[1]["zoning_matter_count"] == 3


def test_median_is_averaged_for_even_counts():
    matters = [
        _matter(2, "2024-01-01", "2024-01-11"),
        _matter(2, "2024-01-01", "2024-01-31"),
    ]
    stats = compute_ward_delay_stats(matters, AS_OF)
    assert stats[2]["zoning_median_days"] == 20.0


def test_sentinel_dates_are_skipped():
    matters = [
        _matter(3, "1900-01-01T00:00:00+00:00", "2024-01-11T00:00:00+00:00"),
        _matter(3, "2024-01-01", "2024-01-11"),
    ]
    stats = compute_ward_delay_stats(matters, AS_OF)
    assert stats[3]["zoning_median_days"] == 10.0
    assert stats[3]["n_resolved"] == 1
    # The sentinel matter still counts toward the ward's total matter count.
    assert stats[3]["zoning_matter_count"] == 2


def test_negative_spans_are_skipped():
    matters = [
        _matter(4, "2024-03-01", "2024-01-01"),
        _matter(4, "2024-01-01", "2024-01-11"),
    ]
    stats = compute_ward_delay_stats(matters, AS_OF)
    assert stats[4]["n_resolved"] == 1
    assert stats[4]["zoning_median_days"] == 10.0


def test_ward_with_no_resolved_matters_has_null_median():
    matters = [_matter(5, "2025-12-01", None, "4-In Committee")]
    stats = compute_ward_delay_stats(matters, AS_OF)
    assert stats[5]["zoning_median_days"] is None
    assert stats[5]["n_pending"] == 1
    assert stats[5]["n_resolved"] == 0


def test_stalled_requires_committee_status_and_180_days():
    matters = [
        # Pending, in committee, 200+ days → stalled
        _matter(6, "2025-06-01", None, "4-In Committee"),
        # Pending, in committee, but only ~30 days → not stalled
        _matter(6, "2025-12-01", None, "4-In Committee"),
        # Pending and old but not in committee → not stalled
        _matter(6, "2025-01-01", None, "2-Introduced"),
        # Resolved → never stalled
        _matter(6, "2024-01-01", "2024-06-01", "90-Final"),
    ]
    stats = compute_ward_delay_stats(matters, AS_OF)
    assert stats[6]["zoning_stalled_count"] == 1
    assert stats[6]["n_pending"] == 3
    assert stats[6]["zoning_matter_count"] == 4


def test_stalled_boundary_is_strictly_greater_than_180_days():
    exactly_180 = [_matter(7, "2025-07-05", None, "4-In Committee")]
    assert (
        compute_ward_delay_stats(exactly_180, date(2026, 1, 1))[7][
            "zoning_stalled_count"
        ]
        == 0
    )
    over_180 = [_matter(7, "2025-07-04", None, "4-In Committee")]
    assert (
        compute_ward_delay_stats(over_180, date(2026, 1, 1))[7]["zoning_stalled_count"]
        == 1
    )


def test_matters_without_a_ward_are_excluded():
    matters = [
        _matter(None, "2024-01-01", "2024-01-11"),
        _matter(8, "2024-01-01", "2024-01-11"),
    ]
    stats = compute_ward_delay_stats(matters, AS_OF)
    assert set(stats) == {8}


def test_unparseable_dates_do_not_crash():
    matters = [_matter(9, "not-a-date", "also-not-a-date")]
    stats = compute_ward_delay_stats(matters, AS_OF)
    assert stats[9]["zoning_median_days"] is None
    assert stats[9]["zoning_matter_count"] == 1


def test_empty_input_returns_empty_stats():
    assert compute_ward_delay_stats([], AS_OF) == {}


# ---------------------------------------------------------------------------
# alder sponsorship
# ---------------------------------------------------------------------------

KNOWN = ["La Spata, Daniel", "Vasquez, Andre Jr.", "Martin, Matthew J."]


def test_is_alder_sponsored_matches_normalized_names():
    matter = {"sponsors": [{"sponsorName": "Ald. Daniel La Spata"}]}
    assert is_alder_sponsored(matter, KNOWN) is True


def test_is_alder_sponsored_false_for_non_alder_sponsor():
    matter = {"sponsors": [{"sponsorName": "Misc. Transmittal"}]}
    assert is_alder_sponsored(matter, KNOWN) is False


def test_is_alder_sponsored_handles_missing_sponsors():
    assert is_alder_sponsored({}, KNOWN) is False
    assert is_alder_sponsored({"sponsors": None}, KNOWN) is False


def test_matched_alder_sponsors_dedupes_and_normalizes():
    matter = {
        "sponsors": [
            {"sponsorName": "La Spata, Daniel"},
            {"sponsorName": "Ald. Daniel La Spata"},
            {"sponsorName": "Martin, Matthew J."},
        ]
    }
    assert matched_alder_sponsors(matter, KNOWN) == [
        "daniel la spata",
        "matthew martin",
    ]


def test_unmatched_sponsor_names_reports_unknown_sponsors():
    matter = {
        "sponsors": [
            {"sponsorName": "La Spata, Daniel"},
            {"sponsorName": "Mayor Brandon Johnson"},
        ]
    }
    assert unmatched_sponsor_names(matter, KNOWN) == ["mayor brandon johnson"]
