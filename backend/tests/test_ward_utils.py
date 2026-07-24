"""Tests for app.imports.sources.ward_utils.parse_ward_number."""

from types import SimpleNamespace

from app.imports.sources.ward_utils import parse_ward_number


def test_parses_ward_from_district_name():
    entity = SimpleNamespace(district_name="Ward 39", district_code=None)
    assert parse_ward_number(entity) == 39


def test_parses_ward_from_district_name_case_insensitive():
    entity = SimpleNamespace(district_name="ward 5", district_code=None)
    assert parse_ward_number(entity) == 5


def test_falls_back_to_numeric_district_code():
    entity = SimpleNamespace(district_name=None, district_code="12")
    assert parse_ward_number(entity) == 12


def test_district_name_takes_precedence_over_code():
    entity = SimpleNamespace(district_name="Ward 7", district_code="99")
    assert parse_ward_number(entity) == 7


def test_returns_none_for_unparseable_district_name():
    entity = SimpleNamespace(district_name="Downtown", district_code=None)
    assert parse_ward_number(entity) is None


def test_returns_none_for_non_numeric_code():
    entity = SimpleNamespace(district_name=None, district_code="abc")
    assert parse_ward_number(entity) is None


def test_returns_none_when_no_district_info():
    entity = SimpleNamespace(district_name=None, district_code=None)
    assert parse_ward_number(entity) is None


def test_handles_missing_attributes():
    assert parse_ward_number(SimpleNamespace()) is None
