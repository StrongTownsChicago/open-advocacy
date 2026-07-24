"""Fetch Chicago ward zoning-delay data from the City Clerk eLMS API.

Sweeps every eLMS matter (paged by skip/top — server-side filters are silently
ignored), keeps the ``ZONING RECLASSIFICATIONS`` matters introduced on or after
the current council term start, detail-fetches each for sponsors/actions,
geocodes the address parsed from the title, assigns a ward by Shapely
point-in-polygon, and writes three committed data modules to ``app/data/``:

- ``ward_zoning_delay_data.py`` — WARD_ZONING_DELAY + ZONING_DELAY_META
- ``zoning_geocode_cache.py``   — ZONING_GEOCODE_CACHE (address → lat/lon/ward)
- ``alder_zoning_candidates.py``— ALDER_ZONING_CANDIDATES (Phase-2 research seed)

Raw pages and matter details are cached under ``backend/.elms_cache/``
(gitignored); the sweep resumes from the cache by default. Wards are NEVER
guessed — an address that fails to geocode or falls outside every ward polygon
is counted against coverage and its record number is listed in the meta.

Usage:
    python -m scripts.fetch_zoning_delay_data                # resume + today's as-of
    python -m scripts.fetch_zoning_delay_data --as-of 2026-07-23
    python -m scripts.fetch_zoning_delay_data --refresh-geocode
    python -m scripts.fetch_zoning_delay_data --no-resume --force
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import aiohttp

from app.core.config import settings
from app.imports.sources.chicago_city_clerk_elms import BASE_URL, normalize_name
from app.imports.sources.zoning_delay import (
    assign_ward,
    compute_ward_delay_stats,
    extract_address_from_title,
    load_ward_polygons,
    matched_alder_sponsors,
    meters_to_ward_boundary,
    unmatched_sponsor_names,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fetch-zoning-delay")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Chicago City Council term that began with the 2023 municipal election.
TERM_START = date(2023, 5, 15)

TARGET_CATEGORY = "ZONING RECLASSIFICATIONS"

PAGE_SIZE = 500  # probed max accepted `top` (1000 → HTTP 400; 500 works)
SWEEP_CONCURRENCY = 3
DETAIL_CONCURRENCY = 2
DETAIL_REQUEST_DELAY = 0.15  # small politeness gap to avoid 429 storms

# Chicago bounding box — geocoded hits outside this are rejected (never assigned).
CHI_LAT_MIN, CHI_LAT_MAX = 41.64, 42.03
CHI_LON_MIN, CHI_LON_MAX = -87.95, -87.52

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_UA = "open-advocacy-zoning-delay/1.0 (github.com/open-advocacy)"
NOMINATIM_MIN_INTERVAL = 1.0  # seconds between requests (usage policy)

COVERAGE_THRESHOLD = 80.0  # refuse to write below this unless --force

# Points within this many meters of their assigned ward boundary are flagged as
# near-boundary — the committed geojson is simplified, so these are the ones a
# more precise map could reassign. Audit-only; does not change ward assignment.
NEAR_BOUNDARY_THRESHOLD_M = 30.0

ALDERPERSON_API_URL = "https://data.cityofchicago.org/resource/c6ie-9e6c.json"

CACHE_DIR = Path(__file__).resolve().parent.parent / ".elms_cache"
PAGE_CACHE_DIR = CACHE_DIR / "pages"
DETAIL_CACHE_DIR = CACHE_DIR / "matters"

DATA_DIR = Path(__file__).resolve().parent.parent / "app" / "data"
DELAY_OUTPUT_PATH = DATA_DIR / "ward_zoning_delay_data.py"
GEOCODE_OUTPUT_PATH = DATA_DIR / "zoning_geocode_cache.py"
CANDIDATES_OUTPUT_PATH = DATA_DIR / "alder_zoning_candidates.py"


# ---------------------------------------------------------------------------
# Committed geocode cache (loaded if present)
# ---------------------------------------------------------------------------


def load_committed_geocode_cache() -> dict[str, dict[str, Any] | None]:
    try:
        from app.data.zoning_geocode_cache import ZONING_GEOCODE_CACHE

        return dict(ZONING_GEOCODE_CACHE)
    except ImportError:
        return {}


# ---------------------------------------------------------------------------
# eLMS sweep (paged, cached, resumable)
# ---------------------------------------------------------------------------


def _parse_intro_date(value: Any) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
    except ValueError:
        return None


MAX_RETRIES = 5
RETRY_BASE_DELAY = 2.0  # seconds; exponential backoff on 429/5xx


async def _get_json(session: aiohttp.ClientSession, url: str) -> tuple[int, Any]:
    """GET a URL with retry/backoff on 429 and 5xx. Returns (status, json|None)."""
    for attempt in range(MAX_RETRIES):
        async with session.get(url) as response:
            if response.status == 404:
                return 404, None
            if response.status == 429 or response.status >= 500:
                delay = RETRY_BASE_DELAY * (2**attempt)
                logger.warning(
                    "HTTP %d for %s; backing off %.1fs (attempt %d/%d)",
                    response.status,
                    url,
                    delay,
                    attempt + 1,
                    MAX_RETRIES,
                )
                await asyncio.sleep(delay)
                continue
            response.raise_for_status()
            return response.status, await response.json(content_type=None)
    raise RuntimeError(f"Exhausted retries for {url}")


async def _fetch_page(
    session: aiohttp.ClientSession,
    semaphore: asyncio.Semaphore,
    skip: int,
    resume: bool,
) -> list[dict[str, Any]]:
    cache_file = PAGE_CACHE_DIR / f"skip_{skip:07d}.json"
    if resume and cache_file.exists():
        return json.loads(cache_file.read_text()).get("data", [])
    async with semaphore:
        url = f"{BASE_URL}/matter?skip={skip}&top={PAGE_SIZE}"
        _, body = await _get_json(session, url)
        cache_file.write_text(json.dumps(body))
        logger.info("Fetched page skip=%d (%d rows)", skip, len(body.get("data", [])))
        return body.get("data", [])


def _page_max_intro(page: list[dict[str, Any]]) -> date | None:
    """The most recent introduction date on a page (None if the page has none)."""
    dates = [
        d
        for m in page
        if (d := _parse_intro_date(m.get("introductionDate"))) is not None
    ]
    return max(dates) if dates else None


async def sweep_matters(resume: bool) -> list[dict[str, Any]]:
    """Page through matters newest-first, stopping once the term start is passed.

    eLMS returns matters newest-first by introduction date and hard-rejects deep
    pagination (skip beyond ~100k → HTTP 400), so we page sequentially in
    concurrency-sized batches and stop after a full batch whose matters all
    predate ``TERM_START`` (one extra batch of margin guards against any
    same-day ordering wobble at the boundary).
    """
    PAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    semaphore = asyncio.Semaphore(SWEEP_CONCURRENCY)

    pages: list[list[dict[str, Any]]] = []
    async with aiohttp.ClientSession() as session:
        meta_url = f"{BASE_URL}/matter?skip=0&top={PAGE_SIZE}"
        async with session.get(meta_url) as response:
            response.raise_for_status()
            meta = (await response.json(content_type=None)).get("meta", {})
        total = int(meta.get("count", 0))
        logger.info("eLMS reports %d total matters (page size %d)", total, PAGE_SIZE)

        all_skips = list(range(0, total, PAGE_SIZE))
        batch_size = SWEEP_CONCURRENCY
        crossed = False
        stop = False
        for i in range(0, len(all_skips), batch_size):
            batch = all_skips[i : i + batch_size]
            batch_pages = await asyncio.gather(
                *[_fetch_page(session, semaphore, s, resume) for s in batch]
            )
            pages.extend(batch_pages)

            batch_max = max(
                (d for p in batch_pages if (d := _page_max_intro(p)) is not None),
                default=None,
            )
            if batch_max is not None and batch_max < TERM_START:
                if crossed:
                    stop = True  # already gave one batch of margin
                crossed = True
                if stop:
                    logger.info(
                        "All matters in batch starting skip=%d predate %s; "
                        "stopping sweep (kept %d pages).",
                        batch[0],
                        TERM_START.isoformat(),
                        len(pages),
                    )
                    break
            else:
                crossed = False

    zoning: list[dict[str, Any]] = []
    for page in pages:
        for matter in page:
            if matter.get("matterCategory") != TARGET_CATEGORY:
                continue
            intro = _parse_intro_date(matter.get("introductionDate"))
            if intro is None or intro < TERM_START:
                continue
            zoning.append(matter)
    logger.info(
        "Found %d %s matters introduced since %s",
        len(zoning),
        TARGET_CATEGORY,
        TERM_START.isoformat(),
    )
    return zoning


async def fetch_detail(
    session: aiohttp.ClientSession,
    semaphore: asyncio.Semaphore,
    guid: str,
    resume: bool,
) -> dict[str, Any] | None:
    cache_file = DETAIL_CACHE_DIR / f"{guid}.json"
    if resume and cache_file.exists():
        return json.loads(cache_file.read_text())
    async with semaphore:
        url = f"{BASE_URL}/matter/{guid}"
        status, data = await _get_json(session, url)
        if status == 404:
            logger.warning("Matter detail not found: %s", guid)
            return None
        cache_file.write_text(json.dumps(data))
        await asyncio.sleep(DETAIL_REQUEST_DELAY)
        return data


async def fetch_details(
    matters: list[dict[str, Any]], resume: bool
) -> dict[str, dict[str, Any]]:
    DETAIL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    semaphore = asyncio.Semaphore(DETAIL_CONCURRENCY)
    details: dict[str, dict[str, Any]] = {}
    async with aiohttp.ClientSession() as session:
        tasks = {
            str(m["matterId"]): fetch_detail(
                session, semaphore, str(m["matterId"]), resume
            )
            for m in matters
        }
        results = await asyncio.gather(*tasks.values())
        for guid, detail in zip(tasks.keys(), results):
            if detail is not None:
                details[guid] = detail
    logger.info("Fetched %d matter details", len(details))
    return details


# ---------------------------------------------------------------------------
# Geocoding (committed cache → Google → Nominatim), never guesses
# ---------------------------------------------------------------------------


class Geocoder:
    def __init__(self, cache: dict[str, dict[str, Any] | None], refresh: bool) -> None:
        self.cache = cache
        self.refresh = refresh
        self._last_nominatim = 0.0
        self._use_google = bool(
            settings.GEOCODING_API_KEY
            and (settings.GEOCODING_SERVICE or "google").lower() == "google"
        )

    def _in_chicago(self, lat: float, lon: float) -> bool:
        return CHI_LAT_MIN <= lat <= CHI_LAT_MAX and CHI_LON_MIN <= lon <= CHI_LON_MAX

    async def _google(
        self, session: aiohttp.ClientSession, query: str
    ) -> tuple[float, float] | None:
        params = {"address": query, "key": settings.GEOCODING_API_KEY or ""}
        try:
            async with session.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params=params,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as response:
                data = await response.json()
            if data.get("status") != "OK" or not data.get("results"):
                return None
            loc = data["results"][0]["geometry"]["location"]
            return float(loc["lat"]), float(loc["lng"])
        except Exception:
            logger.exception("Google geocode failed for %s", query)
            return None

    async def _nominatim(
        self, session: aiohttp.ClientSession, query: str
    ) -> tuple[float, float] | None:
        # Enforce 1 req/s politeness.
        loop = asyncio.get_event_loop()
        wait = NOMINATIM_MIN_INTERVAL - (loop.time() - self._last_nominatim)
        if wait > 0:
            await asyncio.sleep(wait)
        self._last_nominatim = loop.time()
        params = {"q": query, "format": "json", "limit": "1"}
        try:
            async with session.get(
                NOMINATIM_URL,
                params=params,
                headers={"User-Agent": NOMINATIM_UA},
                timeout=aiohttp.ClientTimeout(total=15),
            ) as response:
                if response.status != 200:
                    return None
                results = await response.json()
            if not results:
                return None
            return float(results[0]["lat"]), float(results[0]["lon"])
        except Exception:
            logger.exception("Nominatim geocode failed for %s", query)
            return None

    async def geocode(
        self, session: aiohttp.ClientSession, address: str
    ) -> tuple[float, float] | None:
        """Return (lat, lon) for an address, or None. Uses/updates the cache."""
        if not self.refresh and address in self.cache:
            entry = self.cache[address]
            if entry is None:
                return None
            return entry["lat"], entry["lon"]

        query = f"{address}, Chicago, IL"
        coords: tuple[float, float] | None = None
        if self._use_google:
            coords = await self._google(session, query)
        if coords is None:
            coords = await self._nominatim(session, query)

        if coords is None or not self._in_chicago(*coords):
            if coords is not None:
                logger.warning(
                    "Rejected out-of-Chicago hit for %s: %s", address, coords
                )
            self.cache[address] = None
            return None
        return coords


# ---------------------------------------------------------------------------
# Known alders (current roster from the city data portal)
# ---------------------------------------------------------------------------


async def fetch_known_alders() -> dict[str, str]:
    """Return {normalized_name: display_name} for current alders."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                ALDERPERSON_API_URL, timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                response.raise_for_status()
                rows = await response.json()
    except Exception:
        logger.exception("Failed to fetch alder roster; sponsor matching disabled")
        return {}
    roster: dict[str, str] = {}
    for row in rows:
        raw = row.get("alderman")
        if raw:
            roster[normalize_name(str(raw))] = str(raw)
    logger.info("Loaded %d current alders", len(roster))
    return roster


# ---------------------------------------------------------------------------
# Output writers (generated-file style mirrors existing scripts)
# ---------------------------------------------------------------------------


def _header(lines: list[str]) -> list[str]:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    return [
        "# Auto-generated by scripts/fetch_zoning_delay_data.py",
        "# Source: Chicago City Clerk eLMS API + Nominatim/Google geocoding",
        f"# Generated: {timestamp}",
        *lines,
    ]


def _ruff_format(path: Path) -> None:
    """Best-effort `ruff format` on a generated file so re-runs stay compliant."""
    try:
        subprocess.run(
            [sys.executable, "-m", "ruff", "format", str(path)],
            check=True,
            capture_output=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        logger.warning("Could not ruff-format %s (%s); format it manually.", path, exc)


def write_delay_module(
    ward_stats: dict[int, dict[str, float | int | None]],
    meta: dict[str, Any],
) -> None:
    lines = _header(
        [
            f"# Term start: {meta['term_start']}  |  as-of: {meta['computed_at']}",
            f"# Geocode coverage: {meta['geocode_coverage_pct']}%"
            f" ({meta['total_matters']} matters)",
            "WARD_ZONING_DELAY: dict[int, dict[str, float | int]] = {",
        ]
    )
    for ward in sorted(ward_stats):
        s = ward_stats[ward]
        lines.append(
            f"    {ward}: {{"
            f'"zoning_median_days": {s["zoning_median_days"]}, '
            f'"zoning_matter_count": {s["zoning_matter_count"]}, '
            f'"zoning_stalled_count": {s["zoning_stalled_count"]}}},'
        )
    lines.append("}")
    lines.append("")
    lines.append(f"ZONING_DELAY_META = {json.dumps(meta, indent=4, sort_keys=True)}")
    lines.append("")
    DELAY_OUTPUT_PATH.write_text("\n".join(lines))
    _ruff_format(DELAY_OUTPUT_PATH)
    logger.info("Wrote %s", DELAY_OUTPUT_PATH)


def write_geocode_module(cache: dict[str, dict[str, Any] | None]) -> None:
    lines = _header(
        [
            "# address -> {lat, lon, ward} (ward may be null); None = geocode failure.",
            "# Re-run with --refresh-geocode to retry cached failures.",
            "ZONING_GEOCODE_CACHE: dict[str, dict | None] = {",
        ]
    )
    # Emit Python literals (repr), not JSON — None/ints must round-trip on import.
    for address in sorted(cache):
        entry = cache[address]
        if entry is None:
            lines.append(f"    {address!r}: None,")
        else:
            ordered = {
                "lat": entry["lat"],
                "lon": entry["lon"],
                "ward": entry.get("ward"),
            }
            lines.append(f"    {address!r}: {ordered!r},")
    lines.append("}")
    lines.append("")
    GEOCODE_OUTPUT_PATH.write_text("\n".join(lines))
    _ruff_format(GEOCODE_OUTPUT_PATH)
    logger.info("Wrote %s", GEOCODE_OUTPUT_PATH)


def write_candidates_module(candidates: dict[str, list[dict[str, Any]]]) -> None:
    lines = _header(
        [
            "# Phase-2 research seed: alder-SPONSORED zoning matters, keyed by",
            "# normalized alder name. A matter appears under every alder sponsor.",
            "ALDER_ZONING_CANDIDATES: dict[str, list[dict]] = {",
        ]
    )
    # Emit Python literals (repr), not JSON — None values must round-trip.
    for name in sorted(candidates):
        lines.append(f"    {name!r}: [")
        for item in candidates[name]:
            ordered = dict(sorted(item.items()))
            lines.append(f"        {ordered!r},")
        lines.append("    ],")
    lines.append("}")
    lines.append("")
    CANDIDATES_OUTPUT_PATH.write_text("\n".join(lines))
    _ruff_format(CANDIDATES_OUTPUT_PATH)
    logger.info("Wrote %s", CANDIDATES_OUTPUT_PATH)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


async def run(as_of: date, resume: bool, refresh_geocode: bool, force: bool) -> None:
    ward_polygons = load_ward_polygons()
    geocode_cache = load_committed_geocode_cache()

    zoning_matters = await sweep_matters(resume)
    if not zoning_matters:
        logger.error("No zoning matters found; aborting without writing.")
        return

    details = await fetch_details(zoning_matters, resume)
    known_alders = await fetch_known_alders()

    geocoder = Geocoder(geocode_cache, refresh_geocode)

    enriched: list[dict[str, Any]] = []
    unassigned_records: list[str] = []
    candidates: dict[str, list[dict[str, Any]]] = {}
    unmatched_sponsors: set[str] = set()
    near_boundary_records: list[str] = []

    async with aiohttp.ClientSession() as session:
        for matter in zoning_matters:
            title = matter.get("title")
            record_number = str(matter.get("recordNumber", ""))
            address = extract_address_from_title(title)

            ward: int | None = None
            coords: tuple[float, float] | None = None
            if address is not None:
                cached = geocode_cache.get(address) if not refresh_geocode else None
                if cached is not None and "ward" in cached:
                    ward = cached.get("ward")
                    coords = (cached["lat"], cached["lon"]) if cached else None
                else:
                    coords = await geocoder.geocode(session, address)
                    if coords is not None:
                        ward = assign_ward(coords[0], coords[1], ward_polygons)
                        geocode_cache[address] = {
                            "lat": coords[0],
                            "lon": coords[1],
                            "ward": ward,
                        }

            if ward is None:
                unassigned_records.append(record_number)
            elif coords is not None:
                distance = meters_to_ward_boundary(
                    coords[0], coords[1], ward_polygons, ward
                )
                if distance is not None and distance < NEAR_BOUNDARY_THRESHOLD_M:
                    near_boundary_records.append(record_number)

            enriched.append({**matter, "ward": ward})

            # Candidate seed from the detail payload (sponsors).
            detail = details.get(str(matter.get("matterId")))
            if detail is not None and known_alders:
                matched = matched_alder_sponsors(detail, known_alders)
                unmatched_sponsors.update(unmatched_sponsor_names(detail, known_alders))
                candidate = {
                    "record_number": record_number,
                    "matter_guid": str(matter.get("matterId")),
                    "title": title,
                    "introduction_date": matter.get("introductionDate"),
                    "final_action_date": matter.get("finalActionDate"),
                    "status": matter.get("status"),
                    "ward": ward,
                }
                for name in matched:
                    candidates.setdefault(name, []).append(candidate)

    total = len(enriched)
    assigned = total - len(unassigned_records)
    coverage = round(assigned / total * 100, 1) if total else 0.0
    logger.info("Ward assignment coverage: %.1f%% (%d/%d)", coverage, assigned, total)
    logger.info(
        "Near-boundary (<%.0fm) assignments: %d/%d (%.1f%% of assigned) — "
        "simplified-polygon reassignment risk.",
        NEAR_BOUNDARY_THRESHOLD_M,
        len(near_boundary_records),
        assigned,
        round(len(near_boundary_records) / assigned * 100, 1) if assigned else 0.0,
    )
    if unmatched_sponsors:
        logger.warning(
            "%d sponsor name(s) matched no current alder: %s",
            len(unmatched_sponsors),
            ", ".join(sorted(unmatched_sponsors)),
        )

    ward_stats = compute_ward_delay_stats(enriched, as_of)
    public_stats = {
        ward: {
            "zoning_median_days": s["zoning_median_days"],
            "zoning_matter_count": s["zoning_matter_count"],
            "zoning_stalled_count": s["zoning_stalled_count"],
        }
        for ward, s in ward_stats.items()
    }

    meta = {
        "term_start": TERM_START.isoformat(),
        "computed_at": as_of.isoformat(),
        "total_matters": total,
        "geocode_coverage_pct": coverage,
        "near_boundary_threshold_m": NEAR_BOUNDARY_THRESHOLD_M,
        "near_boundary_count": len(near_boundary_records),
        "near_boundary_record_numbers": sorted(r for r in near_boundary_records if r),
        "unassigned_record_numbers": sorted(r for r in unassigned_records if r),
    }

    # Always write the geocode + candidate caches (they never lose data).
    write_geocode_module(geocode_cache)
    write_candidates_module(candidates)

    if coverage < COVERAGE_THRESHOLD and not force:
        logger.error(
            "Coverage %.1f%% < %.1f%% threshold; NOT writing %s. Use --force to override.",
            coverage,
            COVERAGE_THRESHOLD,
            DELAY_OUTPUT_PATH.name,
        )
        return

    write_delay_module(public_stats, meta)
    logger.info("Done. Coverage %.1f%%, %d wards.", coverage, len(public_stats))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--as-of",
        type=lambda s: date.fromisoformat(s),
        default=date.today(),
        help="Freeze the stalled-in-committee determination at this date (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--no-resume",
        dest="resume",
        action="store_false",
        help="Ignore cached pages/details and re-fetch everything.",
    )
    parser.add_argument(
        "--refresh-geocode",
        action="store_true",
        help="Retry cached geocode failures / re-geocode all addresses.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Write delay data even if ward coverage is below the threshold.",
    )
    args = parser.parse_args()
    asyncio.run(run(args.as_of, args.resume, args.refresh_geocode, args.force))


if __name__ == "__main__":
    main()
