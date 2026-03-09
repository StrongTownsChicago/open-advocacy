"""
Application initialization module.
Handles database setup, admin user creation, and data imports.
"""

import logging
import time
import os

from scripts.init_db import init_db
from scripts.import_data import import_data
from scripts.import_example_project_data import import_projects
from scripts.import_adu_project_data import import_adu_project_data
from app.services.service_factory import (
    get_cached_jurisdiction_service,
    get_cached_project_service,
)

logger = logging.getLogger("open-advocacy")

DB_INIT_LOCK_FILE = "/tmp/open_advocacy_db_initialized"


async def import_chicago_data():
    jurisdiction_service = get_cached_jurisdiction_service()
    chicago_jurisdiction = await jurisdiction_service.find_by_name(
        "Chicago City Council"
    )
    if chicago_jurisdiction:
        logger.info("Chicago jurisdiction already exists, skipping Chicago data import")
    else:
        logger.info("Importing Chicago data...")
        chicago_result = await import_data("chicago")
        if chicago_result.get("steps_failed", 0) > 0:
            logger.warning("Some Chicago import steps failed")


async def import_adu_opt_in_project():
    project_service = get_cached_project_service()
    existing_projects = await project_service.list_projects()
    if existing_projects:
        logger.info("Projects already exist, skipping ADU Opt-In project import")
    else:
        try:
            logger.info("Importing ADU Opt-In project data...")
            await import_adu_project_data()
        except Exception as e:
            logger.error(f"ADU Opt-In project import failed: {str(e)}")


async def import_illinois_data():
    jurisdiction_service = get_cached_jurisdiction_service()
    illinois_house = await jurisdiction_service.find_by_name(
        "Illinois House of Representatives"
    )
    illinois_senate = await jurisdiction_service.find_by_name("Illinois State Senate")
    if illinois_house and illinois_senate:
        logger.info(
            "Illinois jurisdictions already exist, skipping Illinois data import"
        )
    else:
        try:
            logger.info("Importing Illinois data...")
            illinois_result = await import_data("illinois")
            if illinois_result.get("steps_failed", 0) > 0:
                logger.warning("Some Illinois import steps failed")
        except Exception as e:
            logger.error(f"Illinois data import failed: {str(e)}")


async def import_example_projects():
    project_service = get_cached_project_service()
    existing_projects = await project_service.list_projects()
    if existing_projects:
        logger.info("Example projects already exist, skipping project import")
    else:
        try:
            logger.info("Importing example projects...")
            await import_projects()
        except Exception as e:
            logger.error(f"Example project import failed: {str(e)}")


async def initialize_application():
    """
    Initialize the application: database, admin user, and data imports.
    Returns True if initialization was performed, False if skipped.
    """
    logger.info("Starting application initialization check...")

    # Check file-based lock as a backup (for distributed environments)
    if os.path.exists(DB_INIT_LOCK_FILE):
        logger.info("Database initialization lock file exists, skipping initialization")
        return False

    try:
        # Create lock file early to prevent race conditions
        try:
            with open(DB_INIT_LOCK_FILE, "w") as f:
                f.write(
                    f"Database initialization started at {time.strftime('%Y-%m-%d %H:%M:%S')}"
                )
        except Exception as e:
            logger.error(f"Failed to write lock file: {e}")

        logger.info("Initializing database and creating initial admin user...")

        # Step 1: Create database tables
        logger.info("Creating database tables...")
        await init_db(create_tables=True, drop_existing=False)

        # Step 2: Import Chicago data
        await import_chicago_data()

        # Step 3: Import ADU Opt-In project data
        await import_adu_opt_in_project()

        # # Step 4: Import Illinois data
        # await import_illinois_data()

        # # Step 5: Import example projects
        # await import_example_projects()

        logger.info("Database initialization completed successfully")
        return True

    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
