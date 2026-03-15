"""
Application initialization module.
Handles database setup, admin user creation, and data imports.
"""

import logging

from scripts.init_db import init_db, tables_exist
from scripts.import_data import import_data
from scripts.import_example_project_data import import_projects
from scripts.import_adu_project_data import import_adu_project_data
from scripts.import_scorecard_projects import import_scorecard_projects
from app.core.config import settings
from app.db.session import get_engine
from app.models.pydantic.models import UserCreate, UserRole, GroupBase
from app.services.service_factory import (
    get_cached_group_service,
    get_cached_jurisdiction_service,
    get_cached_project_service,
    get_cached_user_service,
)

logger = logging.getLogger("open-advocacy")


async def create_super_admin_if_configured():
    """Create a super admin user if ADMIN_USERNAME and ADMIN_PASSWORD env vars are set."""
    username = settings.ADMIN_USERNAME
    password = settings.ADMIN_PASSWORD
    if not username or not password:
        return

    group_service = get_cached_group_service()
    user_service = get_cached_user_service()

    groups = await group_service.list_groups()
    admin_group = next((g for g in groups if g.name == "Administrators"), None)
    if not admin_group:
        admin_group = await group_service.create_group(
            GroupBase(
                name="Administrators",
                description="Default administrator group with full system access",
            )
        )

    existing_user = await user_service.get_user_by_email(username)
    if existing_user:
        logger.info(f"Super admin '{username}' already exists, skipping creation")
        return

    user_data = UserCreate(
        email=username,
        password=password,
        name="System Administrator",
        role=UserRole.SUPER_ADMIN,
        is_active=True,
        group_id=admin_group.id,
    )
    user = await user_service.create_user(user_data)
    logger.info(f"Created super admin user: {user.email}")


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

    Checks whether the database is already initialized by querying whether
    the 'groups' table exists. If it does, initialization is skipped so that
    persisted data is never wiped on a redeploy. Returns True if
    initialization was performed, False if skipped.
    """
    logger.info("Starting application initialization check...")

    engine = get_engine()
    if await tables_exist(engine):
        logger.info("Database tables already exist, skipping initialization")
        return False

    logger.info("Initializing database and creating initial admin user...")

    # Step 1: Create database tables
    logger.info("Creating database tables...")
    await init_db(create_tables=True)

    # Step 2: Create super admin if configured
    await create_super_admin_if_configured()

    # Step 3: Seed locations based on configuration
    seed_locations = [
        s.strip() for s in settings.SEED_LOCATIONS.split(",") if s.strip()
    ]
    if "chicago" in seed_locations:
        await import_chicago_data()
    if "illinois" in seed_locations:
        await import_illinois_data()

    # Step 4: Seed projects based on configuration
    seed_projects = [s.strip() for s in settings.SEED_PROJECTS.split(",") if s.strip()]
    if "adu" in seed_projects:
        await import_adu_opt_in_project()
    if "example" in seed_projects:
        await import_example_projects()
    if "scorecard" in seed_projects:
        await import_scorecard_projects()

    logger.info("Database initialization completed successfully")
    return True
