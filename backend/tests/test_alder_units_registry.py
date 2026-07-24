"""Validation test for the curated alder units registry (the CI gatekeeper).

Passes trivially while ``ALDER_UNITS_REGISTRY`` is empty (Phase 1). Once the
Phase 2 research workflow appends entries, these checks enforce the curation
rules documented in ``app/data/alder_units_registry.py``.
"""

import re
from datetime import date

import pytest

from app.data.alder_units_registry import ALDER_UNITS_REGISTRY
from app.imports.sources.chicago_city_clerk_elms import normalize_name

VALID_KINDS = {"upzone", "downzone", "shrunk_development"}
RECORD_NUMBER_RE = re.compile(r"^[A-Z]{1,2}\d{4}-\d+$")

# Known alders come from the same committed source the scorecard fetch uses.
# Empty registry never exercises this, but keep resolution honest when populated.
try:
    from app.data.elms_scorecard_data import ELMS_SCORECARD_DATA

    KNOWN_ALDER_NAMES = {
        name for lookup in ELMS_SCORECARD_DATA.values() for name in lookup
    }
except ImportError:  # pragma: no cover
    KNOWN_ALDER_NAMES = set()


def _iso(value: str) -> date:
    return date.fromisoformat(value)


def test_no_duplicate_wards():
    wards = [entry["ward"] for entry in ALDER_UNITS_REGISTRY]
    assert len(wards) == len(set(wards)), "duplicate ward entries in registry"


@pytest.mark.parametrize("entry", ALDER_UNITS_REGISTRY)
def test_registry_entry_is_valid(entry):
    ward = entry["ward"]
    assert isinstance(ward, int) and 1 <= ward <= 50, f"invalid ward {ward}"

    elected = _iso(entry["elected"])

    # Alder resolves against the known roster (skip only if no roster available).
    if KNOWN_ALDER_NAMES:
        assert normalize_name(entry["alder"]) in KNOWN_ALDER_NAMES, (
            f"alder '{entry['alder']}' does not resolve to a known alder"
        )

    assert entry["items"], "registry entry must have at least one item"
    for item in entry["items"]:
        assert item["kind"] in VALID_KINDS, f"invalid kind {item['kind']}"

        delta = item["units_delta"]
        assert isinstance(delta, int) and delta > 0, (
            f"units_delta must be a positive int, got {delta}"
        )

        item_date = _iso(item["date"])
        assert item_date >= elected, (
            f"item date {item_date} precedes alder election {elected}"
        )

        first_public = item.get("first_public_date")
        if first_public is not None:
            assert _iso(first_public) <= item_date, (
                "first_public_date must be on or before date"
            )

        record_number = item.get("elms_record_number")
        if record_number is not None:
            assert RECORD_NUMBER_RE.match(record_number), (
                f"bad record number {record_number}"
            )

        citations = item.get("citations")
        assert citations, "each item requires at least one citation"
        for url in citations:
            assert url.startswith(("http://", "https://")), (
                f"citation must be an http(s) URL, got {url}"
            )
