"""Tests for app.imports.sources.ward_metrics."""

from typing import Any

from app.imports.sources.ward_metrics import (
    aggregate_units_registry,
    build_ward_metric_values,
)


def test_aggregate_empty_registry():
    assert aggregate_units_registry([]) == {}


def test_aggregate_bonus_and_lost_buckets():
    registry = [
        {
            "ward": 1,
            "alder": "Daniel La Spata",
            "elected": "2019-05-20",
            "items": [
                {
                    "name": "up a",
                    "kind": "upzone",
                    "units_delta": 120,
                    "date": "2024-06-12",
                },
                {
                    "name": "up b",
                    "kind": "upzone",
                    "units_delta": 30,
                    "date": "2024-07-01",
                },
                {
                    "name": "down",
                    "kind": "downzone",
                    "units_delta": 10,
                    "date": "2024-08-01",
                },
                {
                    "name": "shrunk",
                    "kind": "shrunk_development",
                    "units_delta": 25,
                    "date": "2024-09-01",
                },
            ],
        }
    ]
    result = aggregate_units_registry(registry)
    assert result[1]["bonus_units"] == 150
    assert result[1]["lost_units"] == 35
    # No item has both first_public_date and date → key omitted.
    assert "mention_to_passage_days" not in result[1]


def test_aggregate_mention_to_passage_median():
    registry = [
        {
            "ward": 5,
            "alder": "X",
            "elected": "2023-05-15",
            "items": [
                {
                    "name": "a",
                    "kind": "upzone",
                    "units_delta": 10,
                    "first_public_date": "2024-01-01",
                    "date": "2024-01-11",  # 10 days
                },
                {
                    "name": "b",
                    "kind": "upzone",
                    "units_delta": 10,
                    "first_public_date": "2024-01-01",
                    "date": "2024-01-31",  # 30 days
                },
                # Missing first_public_date → excluded from the median.
                {
                    "name": "c",
                    "kind": "upzone",
                    "units_delta": 10,
                    "date": "2024-02-01",
                },
            ],
        }
    ]
    result = aggregate_units_registry(registry)
    assert result[5]["mention_to_passage_days"] == 20.0


def test_aggregate_ignores_negative_spans():
    registry = [
        {
            "ward": 7,
            "alder": "X",
            "elected": "2023-05-15",
            "items": [
                {
                    "name": "bad dates",
                    "kind": "upzone",
                    "units_delta": 5,
                    "first_public_date": "2024-03-01",
                    "date": "2024-01-01",  # negative span, skipped
                }
            ],
        }
    ]
    result = aggregate_units_registry(registry)
    assert "mention_to_passage_days" not in result[7]


def test_build_merges_zoning_and_registry():
    zoning: dict[int, dict[str, Any]] = {
        1: {
            "zoning_median_days": 128.0,
            "zoning_matter_count": 14,
            "zoning_stalled_count": 3,
            "n_resolved": 11,
            "n_pending": 3,
        },
        2: {
            "zoning_median_days": None,  # no resolved matter → omitted
            "zoning_matter_count": 2,
            "zoning_stalled_count": 0,
            "n_resolved": 0,
            "n_pending": 2,
        },
    }
    registry = [
        {
            "ward": 1,
            "alder": "Daniel La Spata",
            "elected": "2019-05-20",
            "items": [
                {
                    "name": "up",
                    "kind": "upzone",
                    "units_delta": 100,
                    "date": "2024-06-12",
                }
            ],
        }
    ]
    merged = build_ward_metric_values(zoning_delay=zoning, registry=registry)

    # Ward 1: zoning display keys + registry aggregates; internal keys dropped.
    assert merged[1]["zoning_median_days"] == 128.0
    assert merged[1]["zoning_stalled_count"] == 3
    assert merged[1]["bonus_units"] == 100
    assert merged[1]["lost_units"] == 0
    assert "zoning_matter_count" not in merged[1]
    assert "n_resolved" not in merged[1]

    # Ward 2: null median omitted, but stalled count still surfaces.
    assert "zoning_median_days" not in merged[2]
    assert merged[2]["zoning_stalled_count"] == 0


def test_build_omits_wards_with_no_values():
    zoning: dict[int, dict[str, Any]] = {
        3: {
            "zoning_median_days": None,
            "zoning_matter_count": 1,
            "zoning_stalled_count": 0,
        }
    }
    # zoning_stalled_count 0 is a real value → ward retained.
    merged = build_ward_metric_values(zoning_delay=zoning, registry=[])
    assert merged[3] == {"zoning_stalled_count": 0}


def test_build_with_defaults_returns_dict():
    # Uses committed WARD_ZONING_DELAY + empty ALDER_UNITS_REGISTRY; must not raise.
    assert isinstance(build_ward_metric_values(), dict)
