# Scorecard Zoning Metrics — Methodology & Audit Guide

This document explains the per-alderperson **zoning metrics** added to the Chicago
City Council scorecard (`/scorecard/strong-towns-chicago-chicago-city-council` and
the AHIL Chicago group). It is written for someone with **no prior context** who needs
to verify the numbers are correct, reproduce them, or extend them.

Three metric groups were planned:

| Metric | Status | Source |
|---|---|---|
| **Zoning delay** (median days + stalled count) | **Shipped (Phase 1)** | Fully automated from the City Clerk eLMS API |
| **Bonus units** / **Lost units** | Scaffolded, not yet populated (Phase 2) | Hand/agent-curated registry with mandatory citations |
| **First mention → passage** days | Scaffolded, hidden (Phase 3) | Curated registry |

Only the **delay** metrics are visible in the table today. Bonus/lost-unit columns are
declared but `show_in_table=False` until the curated registry is populated.

---

## 1. Definitions

**Term window.** All zoning-delay figures cover matters **introduced on or after
2023-05-15** (`TERM_START`), the start of the 2023–2027 City Council term. Older matters
are excluded.

**Zoning reclassification.** A Chicago City Council "map amendment" — the ordinance that
rezones a parcel. In eLMS these have `matterCategory == "ZONING RECLASSIFICATIONS"` and
titles like `Zoning Reclassification Map No. 11-J at 4634-4636 N Avers Ave - App No. 23124T1`.

**`zoning_median_days`** (per ward). Median of `finalActionDate − introductionDate` in
days, over the ward's **resolved** reclassifications (those with a real `finalActionDate`).
This is a **ward-scoped** measure of how long rezonings take to clear the ward, not a
personal attribute of the sitting alder. Tooltips say "ward's".

**`zoning_stalled_count`** (per ward). Number of the ward's reclassifications that are
**still in committee more than 180 days** after introduction, as of the frozen `as-of`
date (see below). "In committee" = `finalActionDate` is null **and** the matter status
string contains "In Committee". The 180-day rule is a **proxy** for a stalled application,
not an official designation — re-referred or substituted ordinances can inflate it, which
the tooltip discloses.

**`as-of` date.** The stalled computation needs a "today". It is frozen into the generated
data file (`ZONING_DELAY_META.computed_at`) so the committed numbers are deterministic and
reproducible. The current data was generated with `--as-of 2026-07-23`.

**Bonus units** (Phase 2). Housing units enabled by **alder-initiated** proactive
upzonings since that alder's election. Sum of `units_delta` over registry items with
`kind == "upzone"`.

**Lost units** (Phase 2). Units removed by **alder-initiated** downzonings, plus units cut
from developments shrunk under alder pressure. Sum of `units_delta` over items with
`kind in {"downzone", "shrunk_development"}`. `units_delta` is always stored **positive**;
the `kind` decides the bucket.

**Attribution rule.** Units are credited/debited **only for alder-initiated actions**
(the alder is a sponsor / the action originates from the ward office) — *not* for
applicant-filed reclassifications that merely passed under aldermanic prerogative. This is
a deliberate, narrow definition.

---

## 2. Data lineage

| Metric field | Source API / input | Fetch script | Generated data file | Aggregation | Seeder | API field | Frontend |
|---|---|---|---|---|---|---|---|
| `zoning_median_days`, `zoning_stalled_count` | eLMS `GET /matter` (list) + `/matter/{guid}` (detail) + geocoding | `backend/scripts/fetch_zoning_delay_data.py` | `backend/app/data/ward_zoning_delay_data.py` (`WARD_ZONING_DELAY`, `ZONING_DELAY_META`) | `backend/app/imports/sources/ward_metrics.py::build_ward_metric_values()` | `backend/scripts/import_scorecard_projects.py` → carrier project's `EntityStatusRecord.record_metadata` | `ScorecardEntityRow.metrics[key]` + `ScorecardResponse.metrics[]` | `Scorecard/DesktopTable.tsx` + `MetricCell.tsx` |
| `bonus_units`, `lost_units`, `mention_to_passage_days` | Curated news/ordinance research | (manual + Phase-2 agent workflow) | `backend/app/data/alder_units_registry.py` (`ALDER_UNITS_REGISTRY`) | `ward_metrics.py::aggregate_units_registry()` | same seeder path | same | same |

**Supporting artifacts:**
- `backend/app/data/zoning_geocode_cache.py` (`ZONING_GEOCODE_CACHE`) — committed address→lat/lon/ward cache (1207 addresses, 23 cached failures as `None`). Makes re-runs and CI need no geocoding key.
- `backend/app/data/alder_zoning_candidates.py` (`ALDER_ZONING_CANDIDATES`) — **Phase-2 research seed only** (not used at runtime): alder-sponsored reclassifications keyed by normalized sponsor name (291 rows across 41 alders).
- `backend/app/imports/sources/zoning_delay.py` — network-free pure logic: `extract_address_from_title`, `assign_ward` (Shapely point-in-polygon over `chicago-wards.geojson`), `compute_ward_delay_stats`, `is_alder_sponsored`, `meters_to_ward_boundary`.
- `backend/app/imports/sources/ward_utils.py::parse_ward_number` — shared "Ward N" → int parser (also used by `import_adu_project_data.py`).

**Where values attach (design note).** Metric *descriptors* live on the group's
**position-0 ("carrier") project** `dashboard_config.metrics`; per-alder *values* live in
that same project's `EntityStatusRecord.record_metadata`. This mirrors the existing
`representative_title` convention and needs no schema change. `ScorecardService.get_scorecard`
reads the descriptors from the first project (in position order) that declares any, and
merges declared metric keys from record metadata (lowest-position project wins conflicts).
The existing 6/6 alignment score is **completely independent** — metrics are display-only.

---

## 3. Reproduction

All commands run from `backend/`. The canonical environment is the poetry env
(`poetry install`); a fresh checkout that only needs the tools can use any Python 3.12 with
the pinned `ruff`/`mypy`/`pytest`.

**Regenerate the delay data from scratch** (cold run ≈ 2,570 HTTP requests: ~57 list pages
+ 1,278 matter details + ~1,230 Nominatim geocodes; ~25–30 min, dominated by geocoding at
1 req/s):

```bash
# Optional: set GEOCODING_API_KEY in backend/.env to use Google instead of Nominatim.
python -m scripts.fetch_zoning_delay_data --as-of 2026-07-23
```

The script caches every eLMS page and matter detail under `backend/.elms_cache/`
(gitignored) and every geocode in the committed `zoning_geocode_cache.py`, so **re-runs are
near-instant and make no network calls**:

```bash
python -m scripts.fetch_zoning_delay_data --as-of 2026-07-23   # seconds, fully cached
git diff --stat backend/app/data/ward_zoning_delay_data.py     # should be empty on a clean re-run
```

Flags: `--refresh-geocode` retries the 23 cached geocode failures; `--force` writes even if
ward-assignment coverage falls below the 80% floor (it is currently 95.6%).

**Re-seed the scorecard** (idempotent by slug; safe to re-run):

```bash
python -m scripts.import_scorecard_projects
```

**Verify the numbers surface through the API** (needs the app running with the Chicago group
seeded):

```bash
curl -s localhost:8000/api/scorecard/strong-towns-chicago-chicago-city-council \
  | jq '.metrics, .entities[0].metrics'
```

### Expected figures for the committed data (as-of 2026-07-23)

- Target matters (ZONING RECLASSIFICATIONS since 2023-05-15): **1,278**
- Ward-assignment coverage: **95.6%** (1,222 assigned / 56 unassigned; the 56 record numbers are listed in `ZONING_DELAY_META.unassigned_record_numbers`)
- Per-ward matter count: min **3**, median **18.5**, max **94**; **all 50 wards populated**, all 50 have a median
- Total stalled >180 days: **99**
- Near-boundary points (<30 m from a ward line, reassignment-risk under the simplified polygon): **171 / 1,222 = 14.0%** (`ZONING_DELAY_META.near_boundary_count`)

---

## 4. Auditor checklist

1. **Re-derive one ward's median by hand.** Pick a ward, pull its resolved matters from the
   cache (`backend/.elms_cache/matters/*.json`), compute `finalActionDate − introductionDate`
   for each, take the median, and compare to `WARD_ZONING_DELAY[ward]["zoning_median_days"]`.
   Confirm sentinel dates (`1900-01-01`) and negative spans are excluded.
2. **Check coverage honesty.** Confirm `len(ZONING_DELAY_META["unassigned_record_numbers"])`
   equals `total_matters − assigned`, and that **no ward was assigned by guessing** — every
   unparseable/failed address is in the unassigned list, never dropped into a ward.
3. **Metadata preservation (load-bearing).** The whole feature depends on curated metadata
   surviving the admin refresh. Verify: call the refresh endpoint (or `import_scorecard_projects`)
   twice and diff the carrier project's `record_metadata` — it must be unchanged. This is
   enforced in `StatusService.create_status_record` (`None` = preserve, explicit `{}` = clear)
   and covered by `tests/test_status_service.py::TestCreateStatusRecordPreservesCuratedFields`.
   (Independently reproduced against real SQLite during implementation: three consecutive
   refreshes preserved both `record_metadata` and `notes`.)
4. **Score integrity.** Confirm the alignment score is untouched: the row's `aligned_count` /
   `total_scoreable` must match a pre-change production payload. `tests/test_scorecard_service.py::
   TestGetScorecardMetrics::test_scores_identical_with_and_without_metrics_config` asserts this.
5. **Registry citations (Phase 2).** For a sample of `ALDER_UNITS_REGISTRY` items, open each
   `citations` URL and confirm it supports the `units_delta` and the alder attribution.
   `tests/test_alder_units_registry.py` enforces the structural rules (see §6).
6. **Boundary exposure.** Spot-check a few of the 171 near-boundary record numbers against
   Chicago's official ward map; confirm any misassignment doesn't move a ward's *median*
   materially (medians over ~25 matters/ward are robust to a handful of edge flips).

---

## 5. Known limitations & judgment calls

- **Geocoding failures are never guessed.** 56 matters (4.4%) could not be confidently
  placed in a ward — 23 hard geocode failures, some out-of-Chicago rejects (e.g.
  "400 N Elizabeth Ave" resolving to Waukegan), and titles with no parseable address. They
  are excluded and listed, not distributed into wards.
- **First-address-only rule.** Titles listing multiple addresses are geocoded on the first
  address; address ranges (`4634-4636`) collapse to the first house number.
- **Simplified ward polygons.** `backend/app/data/chicago-wards.geojson` is the correct
  post-2023 official map (verified 5/5 on interior points vs. data-portal `p293-wvbd`) but is
  geometrically simplified, so **14% of points fall within 30 m of a ward boundary** and could
  in principle reassign under the exact boundary. Acceptable for ward-level medians; fully
  auditable via `near_boundary_record_numbers`.
- **Stalled-count proxy.** The ">180 days in committee" rule counts re-referred/substituted
  ordinances as stalled even when they are progressing. Treat `zoning_stalled_count` as a
  signal, not a precise backlog.
- **Ward-scoped, not person-scoped.** Delay metrics describe the **ward** across the whole
  term. Where an alder changed mid-term, some of the ward's delay history predates the sitting
  alder. Unit metrics (Phase 2), by contrast, are per-alder and gated on each alder's
  `elected` date in the registry.
- **Candidate-seed name-normalization gap (Phase 2 action item).** `ALDER_ZONING_CANDIDATES`
  keys sponsors by `normalize_name`. Four sponsor names matched no roster entry: two are
  non-persons ("Misc. Transmittal", "Dept./Agency", expected), but **two are real alders whose
  sponsored matters are currently dropped from the seed** — Carlos Ramirez-Rosa (Ward 35) and
  Walter Burnett Jr. (Ward 27). Reconcile these before the Phase-2 research relies on the seed,
  or their proactive rezonings will be missed. This affects only the research *seed*, not any
  shipped delay number.
- **"Shrunk development" scope.** Counts units removed from a specific project during
  negotiation/downsizing that is attributable to the alder; it does not attempt to model
  hypothetical "could-have-been" capacity.

---

## 6. Registry curation rules (Phase 2)

`ALDER_UNITS_REGISTRY` (in `backend/app/data/alder_units_registry.py`) is a **committed,
reviewed** list — the deliberate opposite of a scraped number. Each item:

```python
{ "ward": 1, "alder": "Daniel La Spata", "elected": "2019-05-20",
  "items": [
    { "name": "2354 N Milwaukee Ave upzone (B3-2 -> B2-5)",
      "kind": "upzone",              # upzone | downzone | shrunk_development
      "units_delta": 120,            # ALWAYS positive; kind decides the bucket
      "date": "2024-06-12",
      "elms_record_number": "O2024-0009123",   # optional cross-reference
      "first_public_date": "2023-11-02",       # optional (newsletter / community meeting)
      "citations": ["https://blockclubchicago.org/..."],  # REQUIRED, >= 1 http(s) URL
      "notes": "..." } ] }
```

Enforced by `backend/tests/test_alder_units_registry.py` (CI is the gatekeeper): ward ∈ 1–50,
no duplicate wards, valid `kind`, `units_delta > 0`, ISO dates, `first_public_date <= date`,
item `date >= elected`, `citations` non-empty and all `http(s)://`, `elms_record_number`
matches `^[A-Z]{1,2}\d{4}-\d+$` when present, and the alder resolves via `normalize_name`.

**Research workflow that populates it** (run separately; produces data, reviewed before commit):
per-alder agents sweep local coverage (Block Club, Crain's, Tribune/Sun-Times, ward newsletters)
since the alder's election for alder-initiated upzones/downzones/shrunk developments, extract
unit counts + dates + earliest public mention, and record **≥1 citation per item** — no
estimates; a number that can't be traced to a citation or ordinance text is omitted and noted.
A second **adversarial verification** agent re-fetches each citation and confirms the number
and attribution before the entry is merged. `ALDER_ZONING_CANDIDATES` seeds the search (subject
to the name-gap caveat in §5). After merge, flip `bonus_units`/`lost_units` to
`show_in_table=True` in `CHICAGO_WARD_METRICS` and re-run the seeder.
