"""Curated registry of alder-initiated housing-production changes (Phase 2).

Hand/agent-curated and reviewed like a data file — every item must carry at
least one citation and survive the validation test in
``tests/test_alder_units_registry.py`` (the CI gatekeeper). Ships **empty** in
Phase 1; the news-research workflow appends entries later.

Aggregation semantics (see ``app.imports.sources.ward_metrics``):
  - ``bonus_units``  = Σ ``units_delta`` over items with ``kind == "upzone"``
  - ``lost_units``   = Σ ``units_delta`` over items with
                       ``kind in {"downzone", "shrunk_development"}``
  - ``mention_to_passage_days`` = median over items that have BOTH
                                  ``first_public_date`` and ``date``

Item schema (all dates are ISO ``YYYY-MM-DD`` strings)::

    ALDER_UNITS_REGISTRY: list[dict] = [
      {
        "ward": 1,                       # int, 1..50, unique per registry entry
        "alder": "Daniel La Spata",      # resolves via normalize_name to a known alder
        "elected": "2019-05-20",         # date the alder took office (window start)
        "items": [
          {
            "name": "2354 N Milwaukee Ave upzone (B3-2 -> B2-5)",
            "kind": "upzone",            # "upzone" | "downzone" | "shrunk_development"
            "units_delta": 120,          # int, ALWAYS POSITIVE; kind decides the bucket
            "date": "2024-06-12",        # date the change took effect (passage)
            "elms_record_number": "O2024-0009123",  # optional; ^[A-Z]{1,2}\\d{4}-\\d+$
            "first_public_date": "2023-11-02",       # optional; <= date
            "citations": ["https://blockclubchicago.org/..."],  # REQUIRED, >= 1, http(s)
            "notes": "...",              # optional free text
          },
        ],
      },
    ]

Hard curation rules (enforced by the validation test):
  - ``units_delta`` is always a positive integer; the sign/bucket is decided by
    ``kind``, never by a negative number.
  - Every item needs >= 1 citation, each an ``http://`` or ``https://`` URL.
  - ``first_public_date <= date`` when both are present.
  - Each item's ``date`` is on or after the alder's ``elected`` date
    (alder-initiated attribution only covers the current term).
  - No duplicate ward across top-level entries; ``ward`` in 1..50.
  - ``elms_record_number`` (when present) matches ``^[A-Z]{1,2}\\d{4}-\\d+$``.
  - ``alder`` resolves via ``normalize_name`` against the known alder roster.
"""

# Ships empty in Phase 1. Phase 2 research appends curated, cited entries.
ALDER_UNITS_REGISTRY: list[dict] = []
