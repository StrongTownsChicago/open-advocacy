"""Tests for app.imports.sources.ward_zoning.compute_rs_percentage."""

from app.imports.sources.ward_zoning import compute_rs_percentage


def test_rs_percentage_single_rs_zone():
    zone_data = [
        {"zone_class": "RS-3", "area_sqft": 30000},
        {"zone_class": "B1-2", "area_sqft": 50000},
        {"zone_class": "RM-5", "area_sqft": 20000},
    ]
    assert compute_rs_percentage(zone_data) == 30.0


def test_rs_percentage_multiple_rs_zones():
    zone_data = [
        {"zone_class": "RS-1", "area_sqft": 10000},
        {"zone_class": "RS-2", "area_sqft": 20000},
        {"zone_class": "RS-3", "area_sqft": 30000},
        {"zone_class": "RT-4", "area_sqft": 40000},
    ]
    assert compute_rs_percentage(zone_data) == 60.0


def test_rs_percentage_zero_when_no_rs_zones():
    zone_data = [
        {"zone_class": "B1-2", "area_sqft": 50000},
        {"zone_class": "RM-5", "area_sqft": 30000},
        {"zone_class": "C1-2", "area_sqft": 20000},
    ]
    assert compute_rs_percentage(zone_data) == 0.0


def test_rs_percentage_zero_when_no_eligible_zones():
    zone_data = [
        {"zone_class": "PD 940", "area_sqft": 50000},
        {"zone_class": "M1-1", "area_sqft": 30000},
        {"zone_class": "PMD 2", "area_sqft": 20000},
    ]
    assert compute_rs_percentage(zone_data) == 0.0


def test_rs_percentage_excludes_non_eligible_zones_from_denominator():
    zone_data = [
        {"zone_class": "RS-3", "area_sqft": 30000},
        {"zone_class": "PD 732", "area_sqft": 200000},
        {"zone_class": "M1-1", "area_sqft": 100000},
        {"zone_class": "T", "area_sqft": 50000},
        {"zone_class": "POS", "area_sqft": 50000},
        {"zone_class": "B1-2", "area_sqft": 70000},
    ]
    # Eligible: RS-3 (30000) + B1-2 (70000) = 100000
    # RS: 30000
    assert compute_rs_percentage(zone_data) == 30.0


def test_rs_percentage_with_empty_data():
    assert compute_rs_percentage([]) == 0.0


def test_rs_percentage_hundred_percent():
    zone_data = [{"zone_class": "RS-3", "area_sqft": 100000}]
    assert compute_rs_percentage(zone_data) == 100.0


def test_rs_percentage_ignores_unknown_prefixes():
    zone_data = [
        {"zone_class": "RS-3", "area_sqft": 30000},
        {"zone_class": "DX-3", "area_sqft": 50000},
        {"zone_class": "B1-2", "area_sqft": 70000},
    ]
    # Eligible: RS-3 (30000) + B1-2 (70000) = 100000 (DX excluded)
    assert compute_rs_percentage(zone_data) == 30.0


def test_rs_percentage_rounding():
    zone_data = [
        {"zone_class": "RS-3", "area_sqft": 33333},
        {"zone_class": "B1-2", "area_sqft": 66667},
    ]
    assert compute_rs_percentage(zone_data) == 33.3


def test_rs_percentage_handles_missing_area_sqft():
    zone_data: list[dict] = [
        {"zone_class": "RS-3"},
        {"zone_class": "B1-2", "area_sqft": 100000},
    ]
    assert compute_rs_percentage(zone_data) == 0.0
