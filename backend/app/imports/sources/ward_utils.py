"""Shared helpers for resolving a Chicago ward number from an entity/district.

Extracted from ``scripts/import_adu_project_data.py`` so both the ADU seeder and
the scorecard ward-metrics seeder resolve wards the same way.
"""

from __future__ import annotations

from typing import Any


def parse_ward_number(entity: Any) -> int | None:
    """Return the ward number for an entity, or None if it can't be determined.

    Prefers a ``district_name`` like ``"Ward 39"``; falls back to a numeric
    ``district_code``. Never guesses — returns None on anything unparseable.
    """
    district_name = getattr(entity, "district_name", None)
    if district_name and district_name.lower().startswith("ward "):
        try:
            return int(district_name.split(" ")[1])
        except (ValueError, IndexError):
            pass

    district_code = getattr(entity, "district_code", None)
    if district_code:
        try:
            return int(district_code)
        except (ValueError, TypeError):
            pass

    return None
