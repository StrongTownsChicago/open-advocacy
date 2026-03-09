import asyncio
import argparse
import logging
import os
import sys
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("db_setup.log"), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("open-advocacy-setup")

try:
    from app.models.orm.models import (
        Base,
        Project,
        Group,
        Entity,
        Jurisdiction,
        EntityStatusRecord,
    )

    logger.info("Successfully imported ORM models")
except ImportError as e:
    logger.error(f"Failed to import ORM models: {str(e)}")
    sys.exit(1)

# Database setup
logger.info(f"Using database URL: {settings.DATABASE_URL}")

# Sample data UUIDs - using predefined UUIDs makes relationships easier to manage
JURISDICTION_IDS = {
    "chicago": UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479"),
    "illinois": UUID("b6a8f7c9-70e1-4f25-9d69-8a17b36cf24c"),
    "cook_county": UUID("d9b15a33-fe8b-4adb-a1c5-2e7e85635d02"),
    "usa": UUID("e5c0b3d7-9a8f-4e21-b6c5-2a9b7c8d3e4f"),
}

PROJECT_IDS = {
    "park_renovation": UUID("1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d"),
    "library_funding": UUID("2b3c4d5e-6f7a-8b9c-0d1e-2f3a4b5c6d7e"),
    "traffic_calming": UUID("3c4d5e6f-7a8b-9c0d-1e2f-3a4b5c6d7e8f"),
    "budget_transparency": UUID("4d5e6f7a-8b9c-0d1e-2f3a-4b5c6d7e8f9a"),
}

ENTITY_IDS = {
    "alderman": UUID("a1b2c3d4-e5f6-4a5b-9c3d-2e1f0a9b8c7d"),
    "state_rep": UUID("b2c3d4e5-f6a7-5b6c-0d1e-3f2a4b5c6d7e"),
    "commissioner": UUID("c3d4e5f6-7a8b-6c7d-1e2f-4a5b6c7d8e9f"),
    "mayor": UUID("d4e5f6a7-8b9c-7d8e-2f3a-5b6c7d8e9f0a"),
    "governor": UUID("e5f6a7b8-9c0d-8e9f-3a4b-6c7d8e9f0a1b"),
}

GROUP_IDS = {
    "park_advocates": UUID("5e6f7a8b-9c0d-1e2f-3a4b-5c6d7e8f9a0b"),
    "taxpayers": UUID("6f7a8b9c-0d1e-2f3a-4b5c-6d7e8f9a0b1c"),
    "library_supporters": UUID("7a8b9c0d-1e2f-3a4b-5c6d-7e8f9a0b1c2d"),
    "safe_streets": UUID("8b9c0d1e-2f3a-4b5c-6d7e-8f9a0b1c2d3e"),
}

STATUS_RECORD_IDS = {
    "alderman_park": UUID("9c0d1e2f-3a4b-5c6d-7e8f-9a0b1c2d3e4f"),
    "state_rep_park": UUID("0d1e2f3a-4b5c-6d7e-8f9a-0b1c2d3e4f5a"),
    "commissioner_library": UUID("1e2f3a4b-5c6d-7e8f-9a0b-1c2d3e4f5a6b"),
    "alderman_library": UUID("2f3a4b5c-6d7e-8f9a-0b1c-2d3e4f5a6b7c"),
    "commissioner_traffic": UUID("3a4b5c6d-7e8f-9a0b-1c2d-3e4f5a6b7c8d"),
    "mayor_traffic": UUID("4b5c6d7e-8f9a-0b1c-2d3e-4f5a6b7c8d9e"),
}


async def init_db(drop_existing: bool = False) -> tuple:
    """Initialize database and return engine and session factory."""
    try:
        # Create data directory if it doesn't exist
        os.makedirs("./data", exist_ok=True)

        # Create engine
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        logger.info("Database engine created")

        # Create database tables
        async with engine.begin() as conn:
            if drop_existing:
                await conn.run_sync(Base.metadata.drop_all)
                logger.info("Dropped all existing tables")

            await conn.run_sync(Base.metadata.create_all)
            logger.info("Created all necessary tables")

        # Create session factory
        async_session = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        logger.info("Session factory created")

        return engine, async_session
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise


async def create_jurisdictions(session: AsyncSession) -> None:
    """Create sample jurisdictions."""
    logger.info("Creating sample jurisdictions...")

    try:
        # Create jurisdictions with preset IDs
        jurisdictions = [
            Jurisdiction(
                id=JURISDICTION_IDS["usa"],
                name="United States",
                description="Federal jurisdiction of the United States",
                level="federal",
                created_at=datetime.now(timezone.utc),
            ),
            Jurisdiction(
                id=JURISDICTION_IDS["illinois"],
                name="Illinois",
                description="State of Illinois jurisdiction",
                level="state",
                created_at=datetime.now(timezone.utc),
            ),
            Jurisdiction(
                id=JURISDICTION_IDS["cook_county"],
                name="Cook County",
                description="Cook County jurisdiction in Illinois",
                level="county",
                created_at=datetime.now(timezone.utc),
            ),
            Jurisdiction(
                id=JURISDICTION_IDS["chicago"],
                name="Chicago",
                description="City of Chicago municipal jurisdiction",
                level="city",
                created_at=datetime.now(timezone.utc),
            ),
        ]

        # Add to database
        session.add_all(jurisdictions)
        await session.commit()
        logger.info(f"Created {len(jurisdictions)} jurisdictions")

    except SQLAlchemyError as e:
        logger.error(f"Error creating jurisdictions: {str(e)}")
        await session.rollback()
        raise


async def create_projects(session: AsyncSession) -> None:
    """Create sample projects."""
    logger.info("Creating sample projects...")

    try:
        # Create projects with preset IDs and direct jurisdiction references
        projects = [
            Project(
                id=PROJECT_IDS["park_renovation"],
                title="Lincoln Park Renovation",
                description="Advocating for the renovation of Lincoln Park with improved playground equipment and better accessibility features.",
                status="active",
                active=True,
                link="https://example.com/park-renovation",
                preferred_status="solid_approval",
                template_response="I am writing to express my strong support for the Lincoln Park renovation project. Our community desperately needs updated playground equipment and improved accessibility features. This project would benefit residents of all ages and abilities. I urge you to support funding for this important community improvement.",
                created_by="admin",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                jurisdiction_id=JURISDICTION_IDS["chicago"],
                group_id=GROUP_IDS["park_advocates"],
            ),
            Project(
                id=PROJECT_IDS["library_funding"],
                title="Public Library Funding",
                description="Supporting increased funding for public libraries to expand digital services and educational programs.",
                status="active",
                active=True,
                link="https://example.com/library-funding",
                preferred_status="solid_approval",
                template_response="I am writing to urge you to support increased funding for our public libraries. Libraries are essential community resources that provide access to information, technology, and educational opportunities for all residents. The proposed funding would allow our libraries to expand digital services and offer more educational programs to serve our diverse community.",
                created_by="admin",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                jurisdiction_id=JURISDICTION_IDS["illinois"],
                group_id=GROUP_IDS["library_supporters"],
            ),
            Project(
                id=PROJECT_IDS["traffic_calming"],
                title="Traffic Calming Measures",
                description="Advocating for speed bumps and improved signage to reduce speeding in residential neighborhoods.",
                status="draft",
                active=True,
                link="https://example.com/traffic-calming",
                preferred_status="leaning_approval",
                template_response="I am writing regarding the concerning issue of speeding in our residential neighborhood. The safety of our children, pedestrians, and cyclists is at risk. I support the implementation of traffic calming measures, including speed bumps and improved signage, to address this problem. These measures have proven effective in similar neighborhoods and would greatly improve safety in our community.",
                created_by="admin",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                jurisdiction_id=JURISDICTION_IDS["chicago"],
                group_id=GROUP_IDS["safe_streets"],
            ),
            Project(
                id=PROJECT_IDS["budget_transparency"],
                title="Budget Transparency Initiative",
                description="Advocating for more transparent budget processes and open data on public spending.",
                status="active",
                active=True,
                link="https://example.com/budget-transparency",
                preferred_status="solid_approval",
                template_response="I am writing to express my support for increased transparency in our government's budgeting process. Citizens have a right to understand how their tax dollars are being spent, and greater transparency would promote accountability and public trust. Please support measures to make budget data more accessible and the budgeting process more open to public input.",
                created_by="admin",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                jurisdiction_id=JURISDICTION_IDS["cook_county"],
                group_id=GROUP_IDS["taxpayers"],
            ),
        ]

        session.add_all(projects)
        await session.commit()
        logger.info(f"Created {len(projects)} projects")

    except SQLAlchemyError as e:
        logger.error(f"Error creating projects: {str(e)}")
        await session.rollback()
        raise


async def create_entities(session: AsyncSession) -> None:
    """Create sample entities (representatives)."""
    logger.info("Creating sample entities...")

    try:
        # Create entities with preset IDs
        entities = [
            Entity(
                id=ENTITY_IDS["alderman"],
                name="Jane Smith",
                title="Alderperson",
                entity_type="alderman",
                jurisdiction_id=JURISDICTION_IDS["chicago"],
                location_module_id="chicago",
                email="jane.smith@chicago.gov",
                phone="(312) 555-1234",
                website="https://www.chicago.gov/ward1",
                address="121 N LaSalle St, Chicago, IL 60602",
                district="Ward 1",
            ),
            Entity(
                id=ENTITY_IDS["state_rep"],
                name="John Doe",
                title="State Representative",
                entity_type="state_rep",
                jurisdiction_id=JURISDICTION_IDS["illinois"],
                location_module_id="illinois",
                email="john.doe@ilga.gov",
                phone="(217) 782-5678",
                website="https://www.ilga.gov/house/rep1",
                address="301 S 2nd St, Springfield, IL 62707",
                district="House District 2",
            ),
            Entity(
                id=ENTITY_IDS["commissioner"],
                name="Sarah Johnson",
                title="County Commissioner",
                entity_type="commissioner",
                jurisdiction_id=JURISDICTION_IDS["cook_county"],
                location_module_id="cook_county",
                email="sarah.johnson@cookcountyil.gov",
                phone="(312) 603-6400",
                website="https://www.cookcountyil.gov/person/sarah-johnson",
                address="118 N Clark St, Chicago, IL 60602",
                district="County Commissioner District 5",
            ),
            Entity(
                id=ENTITY_IDS["mayor"],
                name="Michael Williams",
                title="Mayor",
                entity_type="mayor",
                jurisdiction_id=JURISDICTION_IDS["chicago"],
                location_module_id="chicago",
                email="mayor@chicago.gov",
                phone="(312) 744-3300",
                website="https://www.chicago.gov/mayor",
                address="121 N LaSalle St, Chicago, IL 60602",
            ),
            Entity(
                id=ENTITY_IDS["governor"],
                name="Robert Thompson",
                title="Governor",
                entity_type="governor",
                jurisdiction_id=JURISDICTION_IDS["illinois"],
                location_module_id="illinois",
                email="governor@illinois.gov",
                phone="(217) 782-0244",
                website="https://www.illinois.gov/governor",
                address="207 State House, Springfield, IL 62706",
            ),
        ]

        session.add_all(entities)
        await session.commit()
        logger.info(f"Created {len(entities)} entities")

    except SQLAlchemyError as e:
        logger.error(f"Error creating entities: {str(e)}")
        await session.rollback()
        raise


async def create_groups(session: AsyncSession) -> None:
    """Create sample advocacy groups."""
    logger.info("Creating sample groups...")

    try:
        # Create groups with preset IDs
        groups = [
            Group(
                id=GROUP_IDS["park_advocates"],
                name="Park Advocates",
                description="Group supporting the Lincoln Park renovation proposal",
                created_at=datetime.now(timezone.utc),
            ),
            Group(
                id=GROUP_IDS["taxpayers"],
                name="Taxpayers Association",
                description="Group concerned about the cost of the park renovation",
                created_at=datetime.now(timezone.utc),
            ),
            Group(
                id=GROUP_IDS["library_supporters"],
                name="Library Supporters Coalition",
                description="Alliance of groups advocating for library funding",
                created_at=datetime.now(timezone.utc),
            ),
            Group(
                id=GROUP_IDS["safe_streets"],
                name="Safe Streets Initiative",
                description="Neighborhood group advocating for traffic safety improvements",
                created_at=datetime.now(timezone.utc),
            ),
        ]

        session.add_all(groups)
        await session.commit()
        logger.info(f"Created {len(groups)} groups")

    except SQLAlchemyError as e:
        logger.error(f"Error creating groups: {str(e)}")
        await session.rollback()
        raise


async def create_status_records(session: AsyncSession) -> None:
    """Create sample entity status records."""
    logger.info("Creating sample entity status records...")

    try:
        # Create status records with preset IDs
        status_records = [
            # Park renovation project status records
            EntityStatusRecord(
                id=STATUS_RECORD_IDS["alderman_park"],
                entity_id=ENTITY_IDS["alderman"],
                project_id=PROJECT_IDS["park_renovation"],
                status="solid_approval",
                notes="Expressed strong support for the park renovation during community meeting",
                updated_at=datetime.now(timezone.utc),
                updated_by="admin",
            ),
            EntityStatusRecord(
                id=STATUS_RECORD_IDS["state_rep_park"],
                entity_id=ENTITY_IDS["state_rep"],
                project_id=PROJECT_IDS["park_renovation"],
                status="leaning_approval",
                notes="Generally supportive but has questions about funding sources",
                updated_at=datetime.now(timezone.utc),
                updated_by="admin",
            ),
            # Library funding project status records
            EntityStatusRecord(
                id=STATUS_RECORD_IDS["alderman_library"],
                entity_id=ENTITY_IDS["alderman"],
                project_id=PROJECT_IDS["library_funding"],
                status="neutral",
                notes="Requested more information about the impact on local branch libraries",
                updated_at=datetime.now(timezone.utc),
                updated_by="admin",
            ),
            EntityStatusRecord(
                id=STATUS_RECORD_IDS["commissioner_library"],
                entity_id=ENTITY_IDS["commissioner"],
                project_id=PROJECT_IDS["library_funding"],
                status="solid_approval",
                notes="Has been a long-time advocate for library funding and services",
                updated_at=datetime.now(timezone.utc),
                updated_by="admin",
            ),
            # Traffic calming project status records
            EntityStatusRecord(
                id=STATUS_RECORD_IDS["commissioner_traffic"],
                entity_id=ENTITY_IDS["commissioner"],
                project_id=PROJECT_IDS["traffic_calming"],
                status="leaning_disapproval",
                notes="Concerned about the cost and effectiveness of proposed measures",
                updated_at=datetime.now(timezone.utc),
                updated_by="admin",
            ),
            EntityStatusRecord(
                id=STATUS_RECORD_IDS["mayor_traffic"],
                entity_id=ENTITY_IDS["mayor"],
                project_id=PROJECT_IDS["traffic_calming"],
                status="solid_disapproval",
                notes="Believes other traffic measures would be more effective",
                updated_at=datetime.now(timezone.utc),
                updated_by="admin",
            ),
        ]

        session.add_all(status_records)
        await session.commit()
        logger.info(f"Created {len(status_records)} entity status records")

    except SQLAlchemyError as e:
        logger.error(f"Error creating status records: {str(e)}")
        await session.rollback()
        raise


async def seed_database() -> None:
    """Seed the database with sample data."""
    logger.info("Starting database seeding process...")

    parser = argparse.ArgumentParser(description="Set up the Open Advocacy database")
    parser.add_argument(
        "--drop",
        action="store_true",
        help="Drop existing tables before creating new ones",
    )
    parser.add_argument(
        "--data-only",
        action="store_true",
        help="Only add sample data (assumes tables exist)",
    )
    args = parser.parse_args()

    try:
        # Initialize database
        if args.data_only:
            engine = create_async_engine(settings.DATABASE_URL, echo=False)
            async_session = async_sessionmaker(
                engine, class_=AsyncSession, expire_on_commit=False
            )
            logger.info("Using existing database tables")
        else:
            engine, async_session = await init_db(drop_existing=args.drop)

        # Create a new session for data seeding
        async with async_session() as session:
            # Add data in the correct order to maintain relationships
            await create_jurisdictions(session)
            await create_projects(session)
            await create_entities(session)
            await create_groups(session)
            await create_status_records(session)

        # Clean up
        await engine.dispose()

        logger.info("Database seeding completed successfully!")

    except Exception as e:
        logger.error(f"Database seeding failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(seed_database())
