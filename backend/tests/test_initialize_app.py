"""Tests for scripts/initialize_app.py: initialize_application() orchestration."""

import pytest
from unittest.mock import AsyncMock, patch


class TestInitializeApplication:
    """Tests for initialize_application() flow."""

    async def test_skips_when_tables_already_exist(self):
        """initialize_application() returns False and calls no init/import
        functions when tables_exist() reports the DB is already initialized.
        """
        mock_init_db = AsyncMock()
        mock_import_chicago = AsyncMock()
        mock_import_adu = AsyncMock()

        with (
            patch("scripts.initialize_app.get_engine"),
            patch("scripts.initialize_app.tables_exist", return_value=True),
            patch("scripts.initialize_app.init_db", mock_init_db),
            patch("scripts.initialize_app.import_chicago_data", mock_import_chicago),
            patch("scripts.initialize_app.import_adu_opt_in_project", mock_import_adu),
        ):
            from scripts.initialize_app import initialize_application

            result = await initialize_application()

        assert result is False
        mock_init_db.assert_not_called()
        mock_import_chicago.assert_not_called()
        mock_import_adu.assert_not_called()

    async def test_runs_when_tables_absent(self):
        """initialize_application() returns True and calls init_db
        when tables_exist() reports the DB has no tables yet.
        """
        mock_init_db = AsyncMock(return_value=(None, None))
        mock_import_chicago = AsyncMock()
        mock_import_adu = AsyncMock()

        with (
            patch("scripts.initialize_app.get_engine"),
            patch("scripts.initialize_app.tables_exist", return_value=False),
            patch("scripts.initialize_app.init_db", mock_init_db),
            patch("scripts.initialize_app.import_chicago_data", mock_import_chicago),
            patch("scripts.initialize_app.import_adu_opt_in_project", mock_import_adu),
            patch("scripts.initialize_app.settings") as mock_settings,
        ):
            mock_settings.SEED_LOCATIONS = ""
            mock_settings.SEED_PROJECTS = ""
            from scripts.initialize_app import initialize_application

            result = await initialize_application()

        assert result is True
        mock_init_db.assert_called_once()

    async def test_init_db_called_without_drop_existing(self):
        """When initialization runs, init_db must never be called with
        drop_existing=True.
        """
        mock_init_db = AsyncMock(return_value=(None, None))

        with (
            patch("scripts.initialize_app.get_engine"),
            patch("scripts.initialize_app.tables_exist", return_value=False),
            patch("scripts.initialize_app.init_db", mock_init_db),
            patch("scripts.initialize_app.import_chicago_data", AsyncMock()),
            patch("scripts.initialize_app.import_adu_opt_in_project", AsyncMock()),
            patch("scripts.initialize_app.settings") as mock_settings,
        ):
            mock_settings.SEED_LOCATIONS = ""
            mock_settings.SEED_PROJECTS = ""
            from scripts.initialize_app import initialize_application

            await initialize_application()

        call_kwargs = mock_init_db.call_args.kwargs
        assert call_kwargs.get("drop_existing", False) is not True

    async def test_propagates_tables_exist_error(self):
        """If tables_exist() raises, the exception must propagate out of
        initialize_application() without being swallowed.
        """
        with (
            patch("scripts.initialize_app.get_engine"),
            patch(
                "scripts.initialize_app.tables_exist",
                side_effect=ConnectionError("DB unreachable"),
            ),
        ):
            from scripts.initialize_app import initialize_application

            with pytest.raises(ConnectionError, match="DB unreachable"):
                await initialize_application()

    async def test_propagates_init_db_error(self):
        """If init_db() raises, the exception must propagate out of
        initialize_application() without being swallowed.
        """
        with (
            patch("scripts.initialize_app.get_engine"),
            patch("scripts.initialize_app.tables_exist", return_value=False),
            patch(
                "scripts.initialize_app.init_db",
                side_effect=RuntimeError("Schema creation failed"),
            ),
        ):
            from scripts.initialize_app import initialize_application

            with pytest.raises(RuntimeError, match="Schema creation failed"):
                await initialize_application()


class TestSeedConfiguration:
    """Tests for config-driven seeding in initialize_application()."""

    async def test_initialize_skips_all_seeding_when_seed_vars_empty(self):
        """With SEED_LOCATIONS="" and SEED_PROJECTS="", no import helpers are called."""
        mock_import_chicago = AsyncMock()
        mock_import_illinois = AsyncMock()
        mock_import_adu = AsyncMock()
        mock_import_example = AsyncMock()

        with (
            patch("scripts.initialize_app.get_engine"),
            patch("scripts.initialize_app.tables_exist", return_value=False),
            patch("scripts.initialize_app.init_db", AsyncMock()),
            patch("scripts.initialize_app.import_chicago_data", mock_import_chicago),
            patch("scripts.initialize_app.import_illinois_data", mock_import_illinois),
            patch("scripts.initialize_app.import_adu_opt_in_project", mock_import_adu),
            patch(
                "scripts.initialize_app.import_example_projects", mock_import_example
            ),
            patch("scripts.initialize_app.settings") as mock_settings,
        ):
            mock_settings.SEED_LOCATIONS = ""
            mock_settings.SEED_PROJECTS = ""
            from scripts.initialize_app import initialize_application

            result = await initialize_application()

        assert result is True
        mock_import_chicago.assert_not_called()
        mock_import_illinois.assert_not_called()
        mock_import_adu.assert_not_called()
        mock_import_example.assert_not_called()

    async def test_initialize_seeds_chicago_when_configured(self):
        """SEED_LOCATIONS="chicago" triggers only Chicago import."""
        mock_import_chicago = AsyncMock()
        mock_import_illinois = AsyncMock()
        mock_import_adu = AsyncMock()

        with (
            patch("scripts.initialize_app.get_engine"),
            patch("scripts.initialize_app.tables_exist", return_value=False),
            patch("scripts.initialize_app.init_db", AsyncMock()),
            patch("scripts.initialize_app.import_chicago_data", mock_import_chicago),
            patch("scripts.initialize_app.import_illinois_data", mock_import_illinois),
            patch("scripts.initialize_app.import_adu_opt_in_project", mock_import_adu),
            patch("scripts.initialize_app.import_example_projects", AsyncMock()),
            patch("scripts.initialize_app.settings") as mock_settings,
        ):
            mock_settings.SEED_LOCATIONS = "chicago"
            mock_settings.SEED_PROJECTS = ""
            from scripts.initialize_app import initialize_application

            await initialize_application()

        mock_import_chicago.assert_called_once()
        mock_import_illinois.assert_not_called()
        mock_import_adu.assert_not_called()

    async def test_initialize_seeds_adu_when_configured(self):
        """SEED_PROJECTS="adu" triggers ADU project import."""
        mock_import_chicago = AsyncMock()
        mock_import_adu = AsyncMock()

        with (
            patch("scripts.initialize_app.get_engine"),
            patch("scripts.initialize_app.tables_exist", return_value=False),
            patch("scripts.initialize_app.init_db", AsyncMock()),
            patch("scripts.initialize_app.import_chicago_data", mock_import_chicago),
            patch("scripts.initialize_app.import_illinois_data", AsyncMock()),
            patch("scripts.initialize_app.import_adu_opt_in_project", mock_import_adu),
            patch("scripts.initialize_app.import_example_projects", AsyncMock()),
            patch("scripts.initialize_app.settings") as mock_settings,
        ):
            mock_settings.SEED_LOCATIONS = ""
            mock_settings.SEED_PROJECTS = "adu"
            from scripts.initialize_app import initialize_application

            await initialize_application()

        mock_import_chicago.assert_not_called()
        mock_import_adu.assert_called_once()

    async def test_initialize_seeds_multiple_locations(self):
        """SEED_LOCATIONS="chicago,illinois" triggers both imports."""
        mock_import_chicago = AsyncMock()
        mock_import_illinois = AsyncMock()

        with (
            patch("scripts.initialize_app.get_engine"),
            patch("scripts.initialize_app.tables_exist", return_value=False),
            patch("scripts.initialize_app.init_db", AsyncMock()),
            patch("scripts.initialize_app.import_chicago_data", mock_import_chicago),
            patch("scripts.initialize_app.import_illinois_data", mock_import_illinois),
            patch("scripts.initialize_app.import_adu_opt_in_project", AsyncMock()),
            patch("scripts.initialize_app.import_example_projects", AsyncMock()),
            patch("scripts.initialize_app.settings") as mock_settings,
        ):
            mock_settings.SEED_LOCATIONS = "chicago,illinois"
            mock_settings.SEED_PROJECTS = ""
            from scripts.initialize_app import initialize_application

            await initialize_application()

        mock_import_chicago.assert_called_once()
        mock_import_illinois.assert_called_once()

    async def test_initialize_ignores_whitespace_in_seed_env_vars(self):
        """Whitespace in seed env vars is trimmed correctly."""
        mock_import_chicago = AsyncMock()
        mock_import_illinois = AsyncMock()

        with (
            patch("scripts.initialize_app.get_engine"),
            patch("scripts.initialize_app.tables_exist", return_value=False),
            patch("scripts.initialize_app.init_db", AsyncMock()),
            patch("scripts.initialize_app.import_chicago_data", mock_import_chicago),
            patch("scripts.initialize_app.import_illinois_data", mock_import_illinois),
            patch("scripts.initialize_app.import_adu_opt_in_project", AsyncMock()),
            patch("scripts.initialize_app.import_example_projects", AsyncMock()),
            patch("scripts.initialize_app.settings") as mock_settings,
        ):
            mock_settings.SEED_LOCATIONS = "  chicago , illinois  "
            mock_settings.SEED_PROJECTS = ""
            from scripts.initialize_app import initialize_application

            await initialize_application()

        mock_import_chicago.assert_called_once()
        mock_import_illinois.assert_called_once()

    async def test_initialize_seeds_both_locations_and_projects(self):
        """Both SEED_LOCATIONS and SEED_PROJECTS can be configured together."""
        mock_import_chicago = AsyncMock()
        mock_import_adu = AsyncMock()

        with (
            patch("scripts.initialize_app.get_engine"),
            patch("scripts.initialize_app.tables_exist", return_value=False),
            patch("scripts.initialize_app.init_db", AsyncMock()),
            patch("scripts.initialize_app.import_chicago_data", mock_import_chicago),
            patch("scripts.initialize_app.import_illinois_data", AsyncMock()),
            patch("scripts.initialize_app.import_adu_opt_in_project", mock_import_adu),
            patch("scripts.initialize_app.import_example_projects", AsyncMock()),
            patch("scripts.initialize_app.settings") as mock_settings,
        ):
            mock_settings.SEED_LOCATIONS = "chicago"
            mock_settings.SEED_PROJECTS = "adu"
            from scripts.initialize_app import initialize_application

            await initialize_application()

        mock_import_chicago.assert_called_once()
        mock_import_adu.assert_called_once()
