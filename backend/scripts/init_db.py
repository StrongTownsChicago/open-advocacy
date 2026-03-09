import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

from app.core.config import settings
from app.models.orm.models import Base

logger = logging.getLogger("db-init")


async def init_db(create_tables: bool = True, drop_existing: bool = False):
    """
    Initialize database connection and optionally create tables.

    Args:
        create_tables: Whether to create database tables
        drop_existing: Whether to drop existing tables (only used if create_tables is True)

    Returns:
        Tuple of (engine, async_session_factory)
    """
    try:
        # Create engine
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        logger.info("Database engine created")

        # Create database tables if requested
        if create_tables:
            async with engine.begin() as conn:
                if drop_existing:
                    try:
                        logger.info("Dropping all existing tables...")
                        await conn.run_sync(Base.metadata.drop_all)
                        logger.info("Dropped all existing tables")
                    except Exception as e:
                        logger.error(f"There was an error deleting tables... {e}")

                logger.info("Creating database tables...")
                await conn.run_sync(Base.metadata.create_all)
                logger.info("Created all necessary tables")

        if settings.DATABASE_PROVIDER.lower() == "postgres":
            async with engine.begin() as conn:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
                logger.info("PostGIS extension initialized")

        # Create session factory
        async_session = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        logger.info("Session factory created")

        return engine, async_session
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise


if __name__ == "__main__":
    import argparse
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("db_init.log"),
            logging.StreamHandler(sys.stdout),
        ],
    )

    parser = argparse.ArgumentParser(description="Initialize database")
    parser.add_argument(
        "--drop",
        action="store_true",
        help="Drop existing tables before creating new ones",
    )
    args = parser.parse_args()

    asyncio.run(init_db(create_tables=True, drop_existing=args.drop))
