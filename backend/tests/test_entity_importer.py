"""Tests for EntityImporter._extract_value() — the recursive field extraction logic."""

from unittest.mock import MagicMock

from app.imports.importers.entity_importer import EntityImporter


def _make_importer() -> EntityImporter:
    """Create an EntityImporter with stubbed service dependencies."""
    return EntityImporter(
        entity_service=MagicMock(),
        district_service=MagicMock(),
        jurisdiction_service=MagicMock(),
    )


class TestExtractValue:
    """Tests for _extract_value, the pure data extraction function."""

    def setup_method(self):
        self.importer = _make_importer()

    def test_simple_field(self):
        data = {"name": "Jane Doe", "age": 42}
        assert self.importer._extract_value(data, "name") == "Jane Doe"
        assert self.importer._extract_value(data, "age") == 42

    def test_missing_field_returns_none(self):
        data = {"name": "Jane"}
        assert self.importer._extract_value(data, "email") is None

    def test_none_field_spec_returns_none(self):
        data = {"name": "Jane"}
        assert self.importer._extract_value(data, None) is None

    def test_dot_notation_nested_dict(self):
        data = {"current_role": {"district": "5", "title": "Senator"}}
        assert self.importer._extract_value(data, "current_role.district") == "5"
        assert self.importer._extract_value(data, "current_role.title") == "Senator"

    def test_dot_notation_deeply_nested(self):
        data = {"a": {"b": {"c": "deep_value"}}}
        assert self.importer._extract_value(data, "a.b.c") == "deep_value"

    def test_dot_notation_missing_intermediate_key(self):
        data = {"a": {"b": "value"}}
        assert self.importer._extract_value(data, "a.missing.c") is None

    def test_dot_notation_missing_parent(self):
        data = {"x": "value"}
        assert self.importer._extract_value(data, "missing.child") is None

    def test_array_index_access(self):
        data = {"offices": [{"voice": "555-1234"}, {"voice": "555-5678"}]}
        assert self.importer._extract_value(data, "offices.0.voice") == "555-1234"
        assert self.importer._extract_value(data, "offices.1.voice") == "555-5678"

    def test_array_index_direct_value(self):
        data = {"items": ["first", "second", "third"]}
        assert self.importer._extract_value(data, "items.0") == "first"
        assert self.importer._extract_value(data, "items.2") == "third"

    def test_array_index_out_of_bounds(self):
        data = {"offices": [{"voice": "555-1234"}]}
        assert self.importer._extract_value(data, "offices.5.voice") is None

    def test_array_non_integer_index(self):
        """When parent is a list but next path segment isn't an integer, returns None."""
        data = {"offices": [{"voice": "555-1234"}]}
        assert self.importer._extract_value(data, "offices.voice") is None

    def test_fallback_list_returns_first_truthy(self):
        data = {"city_hall_phone": "555-9999"}
        result = self.importer._extract_value(
            data, ["ward_phone", "city_hall_phone", "mobile"]
        )
        assert result == "555-9999"

    def test_fallback_list_all_missing(self):
        data = {"unrelated": "value"}
        result = self.importer._extract_value(data, ["phone1", "phone2", "phone3"])
        assert result is None

    def test_fallback_list_returns_first_match(self):
        """When multiple fields exist, the first one in the list wins."""
        data = {"ward_phone": "111", "city_hall_phone": "222"}
        result = self.importer._extract_value(data, ["ward_phone", "city_hall_phone"])
        assert result == "111"

    def test_empty_string_parent_in_dot_notation(self):
        """When the parent key exists but its value is falsy (empty string), returns None."""
        data = {"parent": ""}
        assert self.importer._extract_value(data, "parent.child") is None

    def test_none_parent_in_dot_notation(self):
        """When the parent key maps to None, returns None."""
        data = {"parent": None}
        assert self.importer._extract_value(data, "parent.child") is None
