"""Tests for scripts/init_db.py: tables_exist() helper."""

from sqlalchemy.ext.asyncio import create_async_engine

from app.models.orm.models import Base
from scripts.init_db import tables_exist


def make_memory_engine():
    """Return a fresh async in-memory SQLite engine."""
    return create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)


class TestTablesExist:
    """Unit tests for tables_exist() using a real in-memory SQLite engine."""

    async def test_tables_exist_returns_false_on_empty_db(self):
        """tables_exist() must return False when no tables have been created."""
        engine = make_memory_engine()
        try:
            result = await tables_exist(engine)
            assert result is False
        finally:
            await engine.dispose()

    async def test_tables_exist_returns_true_after_create_all(self):
        """tables_exist() must return True after ORM tables are created."""
        engine = make_memory_engine()
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            result = await tables_exist(engine)
            assert result is True
        finally:
            await engine.dispose()

    async def test_tables_exist_is_specific_to_groups_table(self):
        """tables_exist() must return False when only a non-groups table exists.

        This confirms the check is not trivially 'any table exists'.
        """
        engine = make_memory_engine()
        try:
            async with engine.begin() as conn:
                # Create only the jurisdictions table via raw SQL — not 'groups'
                await conn.execute(
                    __import__("sqlalchemy").text(
                        "CREATE TABLE jurisdictions (id TEXT PRIMARY KEY)"
                    )
                )
            result = await tables_exist(engine)
            assert result is False
        finally:
            await engine.dispose()
