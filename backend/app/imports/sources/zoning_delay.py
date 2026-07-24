"""Pure logic for Chicago ward zoning-delay metrics.

Network-free helpers used by ``scripts/fetch_zoning_delay_data.py``:

- :func:`extract_address_from_title` — pull a street address out of an eLMS
  "Zoning Reclassification" matter title.
- :func:`load_ward_polygons` / :func:`assign_ward` — Shapely point-in-polygon
  ward attribution using the committed ``app/data/chicago-wards.geojson``.
- :func:`compute_ward_delay_stats` — median introduction → final-action days and
  stalled-in-committee counts, per ward.
- :func:`is_alder_sponsored` / :func:`matched_alder_sponsors` — alder-initiated
  detection over an eLMS matter detail payload.

Matter dicts use the eLMS field names (``introductionDate``, ``finalActionDate``,
``status``, ``sponsors``) plus an injected ``ward`` key (``int | None``).
"""

from __future__ import annotations

import json
import math
import re
import statistics
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

from shapely.geometry import Point, shape
from shapely.geometry.base import BaseGeometry

from app.imports.sources.chicago_city_clerk_elms import normalize_name

# Matters introduced before this year carry sentinel/garbage dates (e.g. 1900-01-01).
MIN_VALID_YEAR = 2000

# A pending matter counts as "stalled" once it has sat in committee this long.
STALLED_THRESHOLD_DAYS = 180

WARD_GEOJSON_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "chicago-wards.geojson"
)

# "… Map No. 11-J at 4634-4636 N Avers Ave - App No. 23124T1"
# Tolerates "-at", "at7200" (missing space) and doubled spaces.
_AT_MARKER_RE = re.compile(r"(?:^|[\s\-])at[\s\-]*(?=\d)", re.IGNORECASE)

# Trailing application-number suffix, with or without a separating space/hyphen.
_APP_NO_RE = re.compile(r"[\s\-–,]*App(?:lication)?\.?\s*No.*$", re.IGNORECASE)

# Multi-address titles: keep only the first address.
_ADDRESS_SEPARATOR_RE = re.compile(r"\s*(?:,|\band\b|;|/)\s*", re.IGNORECASE)

# "4634-4636 N Avers Ave" / "7108- 7116 S Euclid" → collapse to the first number.
_HOUSE_RANGE_RE = re.compile(r"^(\d+)\s*(?:-|–|to)\s*\d+")

# Minimal shape of a usable address: house number + at least one more word.
_ADDRESS_SHAPE_RE = re.compile(r"^\d+[A-Za-z]?\s+\S+")


def extract_address_from_title(title: str | None) -> str | None:
    """Extract the first street address from a zoning-reclassification title.

    Range addresses collapse to the first house number ("4634-4636 N Avers Ave"
    → "4634 N Avers Ave"); multi-address titles keep the first address only.
    Returns None when nothing parseable is found — never guesses.
    """
    if not title:
        return None

    match = _AT_MARKER_RE.search(title)
    if not match:
        return None

    remainder = title[match.end() :]
    remainder = _APP_NO_RE.sub("", remainder)
    remainder = _ADDRESS_SEPARATOR_RE.split(remainder)[0]
    remainder = remainder.strip().strip("-–,;/ ").strip()
    remainder = re.sub(r"\s+", " ", remainder)

    if not remainder:
        return None

    remainder = _HOUSE_RANGE_RE.sub(r"\1", remainder, count=1).strip()

    if not _ADDRESS_SHAPE_RE.match(remainder):
        return None
    return remainder


def load_ward_polygons(path: Path | str | None = None) -> dict[int, BaseGeometry]:
    """Load ward number → polygon from the committed Chicago wards GeoJSON."""
    geojson_path = Path(path) if path is not None else WARD_GEOJSON_PATH
    with open(geojson_path) as handle:
        data = json.load(handle)

    polygons: dict[int, BaseGeometry] = {}
    for feature in data.get("features", []):
        properties = feature.get("properties") or {}
        raw_ward = properties.get("ward")
        if raw_ward is None:
            continue
        try:
            ward = int(raw_ward)
        except (TypeError, ValueError):
            continue
        polygons[ward] = shape(feature["geometry"])
    return polygons


def assign_ward(
    lat: float | None,
    lon: float | None,
    ward_polygons: dict[int, BaseGeometry],
) -> int | None:
    """Return the ward containing (lat, lon), or None if outside every ward."""
    if lat is None or lon is None:
        return None
    point = Point(lon, lat)
    for ward in sorted(ward_polygons):
        polygon = ward_polygons[ward]
        if polygon.covers(point):
            return ward
    return None


_METERS_PER_DEG_LAT = 111_320.0


def meters_to_ward_boundary(
    lat: float,
    lon: float,
    ward_polygons: dict[int, BaseGeometry],
    ward: int,
) -> float | None:
    """Approx distance (meters) from a point to its assigned ward's boundary.

    Uses a local equirectangular scaling (longitude compressed by cos(lat)),
    which is accurate to well within the tolerance needed for a near-boundary
    audit count at Chicago's latitude. Returns None if the ward is unknown.
    """
    polygon = ward_polygons.get(ward)
    if polygon is None:
        return None
    meters_per_deg_lon = _METERS_PER_DEG_LAT * math.cos(math.radians(lat))
    point = Point(lon * meters_per_deg_lon, lat * _METERS_PER_DEG_LAT)

    def _scale(x: float, y: float) -> tuple[float, float]:
        return x * meters_per_deg_lon, y * _METERS_PER_DEG_LAT

    scaled_boundary = _transform_coords(polygon.boundary, _scale)
    return float(point.distance(scaled_boundary))


def _transform_coords(geometry: BaseGeometry, func: Any) -> BaseGeometry:
    """Apply a (x, y) -> (x, y) function to every coordinate in a geometry."""
    from shapely.ops import transform

    return transform(lambda x, y, z=None: func(x, y), geometry)


def _parse_elms_date(value: Any) -> date | None:
    """Parse an eLMS timestamp, rejecting sentinel dates before MIN_VALID_YEAR."""
    if not value:
        return None
    if isinstance(value, datetime):
        parsed = value.date()
    elif isinstance(value, date):
        parsed = value
    else:
        text = str(value).strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(text).date()
        except ValueError:
            try:
                parsed = datetime.strptime(text[:10], "%Y-%m-%d").date()
            except ValueError:
                return None
    if parsed.year < MIN_VALID_YEAR:
        return None
    return parsed


def _is_in_committee(status: Any) -> bool:
    return "in committee" in str(status or "").lower()


def compute_ward_delay_stats(
    matters: Iterable[dict[str, Any]],
    as_of: date,
) -> dict[int, dict[str, float | int | None]]:
    """Aggregate zoning introduction → final-action delay statistics per ward.

    Args:
        matters: eLMS matter dicts with an injected ``ward`` key. Matters with
            ``ward`` of None are ignored (never guessed into a ward).
        as_of: the date the "stalled" determination is frozen against.

    Returns:
        ward → {zoning_median_days, zoning_matter_count, zoning_stalled_count,
        n_resolved, n_pending}. ``zoning_median_days`` is None when the ward has
        no resolved matter with usable dates.
    """
    spans: dict[int, list[int]] = {}
    counts: dict[int, int] = {}
    stalled: dict[int, int] = {}
    pending: dict[int, int] = {}

    for matter in matters:
        ward = matter.get("ward")
        if not isinstance(ward, int):
            continue
        counts[ward] = counts.get(ward, 0) + 1
        spans.setdefault(ward, [])
        stalled.setdefault(ward, 0)
        pending.setdefault(ward, 0)

        introduced = _parse_elms_date(matter.get("introductionDate"))
        finalized = _parse_elms_date(matter.get("finalActionDate"))

        if finalized is not None:
            if introduced is not None and (finalized - introduced).days >= 0:
                spans[ward].append((finalized - introduced).days)
            continue

        pending[ward] += 1
        if (
            introduced is not None
            and _is_in_committee(matter.get("status"))
            and (as_of - introduced).days > STALLED_THRESHOLD_DAYS
        ):
            stalled[ward] += 1

    stats: dict[int, dict[str, float | int | None]] = {}
    for ward in sorted(counts):
        ward_spans = spans[ward]
        stats[ward] = {
            "zoning_median_days": (
                round(float(statistics.median(ward_spans)), 1) if ward_spans else None
            ),
            "zoning_matter_count": counts[ward],
            "zoning_stalled_count": stalled[ward],
            "n_resolved": len(ward_spans),
            "n_pending": pending[ward],
        }
    return stats


def matched_alder_sponsors(
    matter: dict[str, Any],
    known_alder_names: Iterable[str],
) -> list[str]:
    """Return the normalized names of the matter's sponsors who are known alders."""
    known = {normalize_name(name) for name in known_alder_names}
    matched: list[str] = []
    for sponsor in matter.get("sponsors") or []:
        raw = sponsor.get("sponsorName")
        if not raw:
            continue
        normalized = normalize_name(str(raw))
        if normalized in known and normalized not in matched:
            matched.append(normalized)
    return matched


def unmatched_sponsor_names(
    matter: dict[str, Any],
    known_alder_names: Iterable[str],
) -> list[str]:
    """Return normalized sponsor names that match no known alder (for logging)."""
    known = {normalize_name(name) for name in known_alder_names}
    unmatched: list[str] = []
    for sponsor in matter.get("sponsors") or []:
        raw = sponsor.get("sponsorName")
        if not raw:
            continue
        normalized = normalize_name(str(raw))
        if normalized not in known and normalized not in unmatched:
            unmatched.append(normalized)
    return unmatched


def is_alder_sponsored(
    matter: dict[str, Any],
    known_alder_names: Iterable[str],
) -> bool:
    """True when at least one of the matter's sponsors is a known alder."""
    return bool(matched_alder_sponsors(matter, known_alder_names))
