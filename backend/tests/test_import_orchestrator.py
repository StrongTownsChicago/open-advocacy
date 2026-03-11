"""Tests for ImportOrchestrator — step execution, validation, and error handling."""

from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.imports.orchestrator import ImportOrchestrator
from app.imports.locations.base import LocationConfig


class FakeLocationConfig(LocationConfig):
    """A minimal location config for testing."""

    @property
    def name(self) -> str:
        return "Test Location"

    @property
    def description(self) -> str:
        return "A test location"

    @property
    def import_steps(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "step_one",
                "importer": "fake_importer",
                "data_source": "fake_source",
                "config": {"jurisdiction_name": "Test"},
            },
            {
                "name": "step_two",
                "importer": "fake_importer",
                "config": {"jurisdiction_name": "Test"},
            },
        ]

    async def get_importers(self) -> dict[str, Any]:
        fake_importer = AsyncMock()
        fake_importer.validate_import = AsyncMock(return_value=True)
        fake_importer.import_data = AsyncMock(return_value={"created": 5})

        fake_source = AsyncMock()
        fake_source.fetch_data = AsyncMock(return_value=[{"name": "Test Entity"}])

        return {
            "importers": {"fake_importer": fake_importer},
            "data_sources": {"fake_source": fake_source},
        }


class TestImportOrchestrator:
    def setup_method(self):
        self.orchestrator = ImportOrchestrator()

    async def test_unknown_location_raises(self):
        with pytest.raises(ValueError, match="Unknown location"):
            await self.orchestrator.import_location("nonexistent")

    async def test_registered_location_executes_steps(self):
        self.orchestrator.register_location("test", FakeLocationConfig)
        result = await self.orchestrator.import_location("test")

        assert result["location"] == "test"
        assert result["steps_total"] == 2
        assert result["steps_succeeded"] == 2
        assert result["steps_failed"] == 0

    async def test_step_with_invalid_importer_reports_error(self):
        """A step referencing a nonexistent importer should report an error, not crash."""

        class BadImporterConfig(FakeLocationConfig):
            @property
            def import_steps(self) -> list[dict[str, Any]]:
                return [
                    {
                        "name": "bad_step",
                        "importer": "nonexistent_importer",
                        "config": {},
                    }
                ]

        self.orchestrator.register_location("bad", BadImporterConfig)
        result = await self.orchestrator.import_location("bad")

        assert result["steps_failed"] == 1
        assert "Invalid importer" in result["results"][0]["message"]

    async def test_step_with_invalid_data_source_reports_error(self):
        """A step referencing a nonexistent data source should report an error."""

        class BadSourceConfig(FakeLocationConfig):
            @property
            def import_steps(self) -> list[dict[str, Any]]:
                return [
                    {
                        "name": "bad_source_step",
                        "importer": "fake_importer",
                        "data_source": "nonexistent_source",
                        "config": {},
                    }
                ]

        self.orchestrator.register_location("bad_source", BadSourceConfig)
        result = await self.orchestrator.import_location("bad_source")

        assert result["steps_failed"] == 1
        assert "Invalid data source" in result["results"][0]["message"]

    async def test_skip_step_via_kwargs(self):
        """Steps can be skipped by passing step_name.skip=True."""
        self.orchestrator.register_location("test", FakeLocationConfig)
        result = await self.orchestrator.import_location(
            "test", **{"step_one.skip": True}
        )

        assert result["steps_total"] == 2
        # Only step_two executed
        assert result["steps_succeeded"] == 1
        assert len(result["results"]) == 1
        assert result["results"][0]["step"] == "step_two"

    async def test_data_fetch_error_reports_cleanly(self):
        """If a data source fails to fetch, the step should report an error."""

        class FailingSourceConfig(FakeLocationConfig):
            async def get_importers(self) -> dict[str, Any]:
                fake_importer = AsyncMock()
                fake_importer.validate_import = AsyncMock(return_value=True)

                fake_source = AsyncMock()
                fake_source.fetch_data = AsyncMock(
                    side_effect=RuntimeError("Connection timeout")
                )

                return {
                    "importers": {"fake_importer": fake_importer},
                    "data_sources": {"fake_source": fake_source},
                }

        self.orchestrator.register_location("fail", FailingSourceConfig)
        result = await self.orchestrator.import_location("fail")

        failed_steps = [r for r in result["results"] if r["status"] == "error"]
        assert len(failed_steps) >= 1
        assert "Connection timeout" in failed_steps[0]["message"]

    async def test_validation_failure_reports_error(self):
        """If importer validation fails, the step should report an error."""

        class FailValidationConfig(FakeLocationConfig):
            @property
            def import_steps(self) -> list[dict[str, Any]]:
                return [
                    {
                        "name": "validate_fail",
                        "importer": "strict_importer",
                        "config": {},
                    }
                ]

            async def get_importers(self) -> dict[str, Any]:
                strict_importer = AsyncMock()
                strict_importer.validate_import = AsyncMock(return_value=False)

                return {
                    "importers": {"strict_importer": strict_importer},
                    "data_sources": {},
                }

        self.orchestrator.register_location("strict", FailValidationConfig)
        result = await self.orchestrator.import_location("strict")

        assert result["steps_failed"] == 1
        assert "Validation failed" in result["results"][0]["message"]

    async def test_get_available_locations(self):
        self.orchestrator.register_location("test", FakeLocationConfig)
        locations = await self.orchestrator.get_available_locations()

        assert len(locations) == 1
        assert locations[0]["key"] == "test"
        assert locations[0]["name"] == "Test Location"
        assert locations[0]["steps"] == 2
