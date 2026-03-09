import asyncio
import argparse
import logging
import os
import sys
import uuid
import aiohttp
import random
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from app.core.config import settings


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("chicago_import.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("chicago-import")

try:
    from app.models.orm.models import (
        Base,
        Project,
        Group,
        Entity,
        Jurisdiction,
        EntityStatusRecord,
        District,
    )

    logger.info("Successfully imported ORM models")
except ImportError as e:
    logger.error(f"Failed to import ORM models: {str(e)}")
    sys.exit(1)

# Database setup
DATABASE_URL = settings.DATABASE_URL
logger.info(f"Using database URL: {DATABASE_URL}")

# Chicago API endpoint
CHICAGO_ALDERMEN_API = "https://data.cityofchicago.org/resource/c6ie-9e6c.json"

# Define UUIDs
CHICAGO_ID = UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479")
CHICAGO_COUNCIL_ID = UUID("a7b8c9d0-e1f2-3a4b-5c6d-7e8f9a0b1c2d")
STRONG_TOWNS_GROUP_ID = UUID("4b5c6d7e-8f9a-0b1c-2d3e-4f5a6b7c8d9e")

# Project UUIDs
HOUSING_PROJECT_ID = UUID("d4e5f6a7-8b9c-7d8e-2f3a-5b6c7d8e9f0a")
PARKING_REFORM_PROJECT_ID = UUID("f6a7b8c9-0d1e-9f0a-4b5c-7d8e9f0a1b2c")
TWO_TO_FOUR_FLATS_PROJECT_ID = UUID("a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d")
SPEED_LIMIT_PROJECT_ID = UUID("b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e")
VACANCY_TAX_PROJECT_ID = UUID("c3d4e5f6-a7b8-9c0d-1e2f-3a4b5c6d7e8f")
BROADWAY_UPZONING_PROJECT_ID = UUID("d4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f9a")
MARCEY_DEVELOPMENT_PROJECT_ID = UUID("e5f6a7b8-c9d0-1e2f-3a4b-5c6d7e8f9a0b")
FERN_HILL_PROJECT_ID = UUID("f6a7b8c9-d0e1-2f3a-4b5c-6d7e8f9a0b1c")


async def init_db(create_tables: bool = False, drop_existing: bool = False) -> tuple:
    """Initialize database and return engine and session factory."""
    try:
        # Create data directory if it doesn't exist
        os.makedirs("./data", exist_ok=True)

        # Create engine
        engine = create_async_engine(DATABASE_URL, echo=False)
        logger.info("Database engine created")

        # Create database tables if requested
        if create_tables:
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


async def fetch_chicago_aldermen():
    """Fetch Chicago aldermen data from the API."""
    logger.info(f"Fetching Chicago aldermen data from: {CHICAGO_ALDERMEN_API}")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(CHICAGO_ALDERMEN_API) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Successfully fetched data for {len(data)} aldermen")
                    return data
                else:
                    logger.error(f"Failed to fetch data: {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Error fetching aldermen data: {str(e)}")
        return None


async def create_chicago_council_jurisdiction(session: AsyncSession) -> UUID:
    """Create Chicago City Council jurisdiction."""
    logger.info("Creating Chicago City Council jurisdiction...")

    try:
        # Create Chicago City Council jurisdiction
        chicago_council = Jurisdiction(
            id=CHICAGO_COUNCIL_ID,
            name="Chicago City Council",
            description="Legislative branch of the City of Chicago government consisting of 50 alderpersons",
            level="city_council",
            created_at=datetime.now(timezone.utc),
        )

        session.add(chicago_council)
        await session.commit()
        logger.info(
            f"Created Chicago City Council jurisdiction with ID: {CHICAGO_COUNCIL_ID}"
        )

        return CHICAGO_COUNCIL_ID
    except SQLAlchemyError as e:
        logger.error(f"Error creating Chicago City Council jurisdiction: {str(e)}")
        await session.rollback()
        raise


async def create_strong_towns_group(session: AsyncSession) -> UUID:
    """Create Strong Towns Chicago advocacy group."""
    logger.info("Creating Strong Towns Chicago group...")

    try:
        group = Group(
            id=STRONG_TOWNS_GROUP_ID,
            name="Strong Towns Chicago",
            description="Empowers neighborhoods to incrementally build a more financially resilient city from the bottom up, through abundant housing, safe streets, and effective transportation.",
            created_at=datetime.now(timezone.utc),
        )

        session.add(group)
        await session.commit()
        logger.info(
            f"Created Strong Towns Chicago group with ID: {STRONG_TOWNS_GROUP_ID}"
        )

        return STRONG_TOWNS_GROUP_ID
    except SQLAlchemyError as e:
        logger.error(f"Error creating Strong Towns Chicago group: {str(e)}")
        await session.rollback()
        raise


async def create_aldermen_entities(
    session: AsyncSession, aldermen_data, jurisdiction_id: UUID
):
    """Create entity records for Chicago aldermen."""
    logger.info("Creating Chicago aldermen entities...")

    try:
        entities = []
        # Track districts we've created
        district_map: dict[str, Any] = {}

        for alderman in aldermen_data:
            # Extract name
            name = alderman.get("alderman", "")

            # Extract ward number
            ward = alderman.get("ward", "")
            district_name = f"Ward {ward}"

            # Get or create district
            if district_name in district_map:
                district_id = district_map[district_name]
            else:
                # Create new district
                district = District(
                    id=uuid.uuid4(),
                    name=district_name,
                    code=ward,
                    jurisdiction_id=jurisdiction_id,
                )
                session.add(district)
                await session.flush()  # Get ID without full commit
                district_id = district.id
                district_map[district_name] = district_id

            # Extract contact info
            email = alderman.get("email", "")
            ward_phone = alderman.get("ward_phone", "")
            city_hall_phone = alderman.get("city_hall_phone", "")
            phone = ward_phone if ward_phone else city_hall_phone

            # Address logic
            ward_address = alderman.get("address", "")
            zipcode = alderman.get("zipcode", "")
            city_hall_address = alderman.get("city_hall_address", "")
            city_hall_zipcode = alderman.get("city_hall_zipcode", "")

            if ward_address:
                full_address = f"{ward_address}, Chicago, IL {zipcode}"
            else:
                full_address = f"{city_hall_address}, Chicago, IL {city_hall_zipcode}"

            website = None
            if "website" in alderman and isinstance(alderman["website"], dict):
                website = alderman["website"].get("url", None)

            entity = Entity(
                id=uuid.uuid4(),
                name=name,
                title="Alderperson",
                entity_type="alderman",
                district_id=district_id,
                email=email,
                phone=phone,
                website=website,
                address=full_address,
                jurisdiction_id=jurisdiction_id,
            )

            entities.append(entity)

        # Add all entities to database
        session.add_all(entities)
        await session.commit()
        logger.info(f"Created {len(entities)} aldermen entities")

        return entities
    except SQLAlchemyError as e:
        logger.error(f"Error creating aldermen entities: {str(e)}")
        await session.rollback()
        raise


async def create_strong_towns_projects(
    session: AsyncSession, jurisdiction_id: UUID, group_id: UUID
):
    """Create projects for Strong Towns Chicago initiatives."""
    logger.info("Creating Strong Towns Chicago projects...")

    try:
        # Housing Project - ADUs
        housing_project = Project(
            id=HOUSING_PROJECT_ID,
            title="Accessory Dwelling Units Legalization",
            description="Advocating for legalizing accessory dwelling units (ADUs) throughout Chicago and Illinois to increase housing supply and affordability while allowing for gentle density increases in existing neighborhoods.",
            status="active",
            active=True,
            link="https://actionnetwork.org/petitions/support-adus-citywide-in-chicago",
            preferred_status="solid_approval",
            template_response="I am writing to express my strong support for legalizing accessory dwelling units throughout Chicago and Illinois. ADUs provide affordable housing options, help homeowners with mortgage costs, allow for aging in place, and increase density without changing neighborhood character. They're a proven solution to our housing shortage that has worked well in other cities. I urge you to support ADU legalization to help build a more financially resilient Chicago with housing options for everyone.",
            created_by="admin",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            jurisdiction_id=jurisdiction_id,
            group_id=group_id,
        )

        # Allow 2-4 Flats By Right
        two_to_four_flats_project = Project(
            id=TWO_TO_FOUR_FLATS_PROJECT_ID,
            title="2-4 Flat By-Right Zoning Reform",
            description="Advocating for changes to Chicago's zoning laws to allow 2-to-4-flat buildings by right in residential areas, helping to increase the supply of affordable housing and reverse the trend of losing these traditional Chicago housing types.",
            status="active",
            active=True,
            link="https://actionnetwork.org/petitions/support-4-flats-by-right-throughout-chicago/",
            preferred_status="solid_approval",
            template_response="I support updating Chicago's zoning to allow 2-to-4-flat buildings by right in residential areas. These traditional Chicago housing types provide naturally affordable homes, allow multi-generational living, and help maintain neighborhood character while increasing density. Recent decades have seen thousands of these structures converted to single-family homes, reducing affordable housing options. I urge you to support zoning reform that makes it easier to build and maintain 2-4 flats throughout Chicago.",
            created_by="admin",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            jurisdiction_id=jurisdiction_id,
            group_id=group_id,
        )

        # Speed Limit Reduction
        speed_limit_project = Project(
            id=SPEED_LIMIT_PROJECT_ID,
            title="Lower City Speed Limit to 25 MPH",
            description="Supporting efforts to reduce Chicago's default speed limit from 30 mph to 25 mph to improve safety for pedestrians, cyclists, and all road users. Research shows that lower speeds dramatically reduce the likelihood of fatal crashes.",
            status="active",
            active=True,
            link="https://actionnetwork.org/letters/lower-the-default-speed-limit-in-chicago",
            preferred_status="solid_approval",
            template_response="I strongly support reducing Chicago's default speed limit from 30 mph to 25 mph. Data shows this small reduction can cut pedestrian fatality risks in half when crashes occur. Other major cities like New York, Boston, and Seattle have already implemented this change with positive results for public safety. I urge you to support this important safety measure to protect all Chicagoans and create more livable streets for everyone.",
            created_by="admin",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            jurisdiction_id=jurisdiction_id,
            group_id=group_id,
        )

        # Parking Minimum Reform
        parking_reform_project = Project(
            id=PARKING_REFORM_PROJECT_ID,
            title="Parking Minimum Elimination",
            description="Advocating for the elimination of parking minimums in Chicago's zoning code to enable more affordable housing development, reduce car dependency, and create more walkable neighborhoods.",
            status="active",
            active=True,
            link="https://chicago-parking-reform.org/",
            preferred_status="solid_approval",
            template_response="I am writing to express my support for eliminating parking minimums in Chicago's zoning code. Current requirements force developers to build expensive parking spaces regardless of actual demand, which increases housing costs, wastes valuable urban land, and encourages more car use and traffic congestion. By eliminating these outdated requirements, we can make housing more affordable, enable small-scale neighborhood development, and create a more walkable, sustainable city. Many successful cities have already made this change with positive results. I urge you to support this important reform.",
            created_by="admin",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            jurisdiction_id=jurisdiction_id,
            group_id=group_id,
        )

        # Vacancy Tax
        vacancy_tax_project = Project(
            id=VACANCY_TAX_PROJECT_ID,
            title="Vacancy Tax Implementation",
            description="Advocating for the implementation of vacancy taxes in high-demand Chicago neighborhoods to discourage property speculation, reduce empty storefronts and homes, and generate revenue for affordable housing initiatives.",
            status="active",
            active=True,
            link="https://lawreview.uchicago.edu/sites/default/files/2024-09/03_Dong_CMT_Final.pdf",
            preferred_status="solid_approval",
            template_response="I support implementing vacancy taxes in high-demand Chicago neighborhoods. Vacant properties negatively impact community safety, economic vitality, and housing affordability while property owners wait for values to increase. A vacancy tax would discourage speculation, incentivize productive use of properties, and generate funding for affordable housing initiatives. Cities like Vancouver and San Francisco have implemented similar policies with success. I urge you to support this measure to create more vibrant, affordable neighborhoods.",
            created_by="admin",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            jurisdiction_id=jurisdiction_id,
            group_id=group_id,
        )

        # Broadway Upzoning
        broadway_upzoning_project = Project(
            id=BROADWAY_UPZONING_PROJECT_ID,
            title="Broadway Corridor Upzoning",
            description="Supporting the Chicago Department of Planning and Development's initiative to upzone Broadway from Montrose Avenue to Devon Avenue, allowing for increased density, more housing, and pedestrian-friendly development along this key transit corridor.",
            status="active",
            active=True,
            link="https://chi.streetsblog.org/2025/01/06/now-playing-on-broadway-new-land-use-plan-could-support-edgewater-uptown-and-the-entire-city",
            preferred_status="solid_approval",
            template_response="I strongly support the proposed upzoning of Broadway from Montrose to Devon Avenue. This transit-rich corridor is ideal for increased density that would provide more housing, support local businesses, and create a more vibrant, walkable community. With the CTA Red Line modernization nearing completion, now is the perfect time to encourage development that maximizes this infrastructure investment. The proposed upzoning to B3-5 and C1-5 designations with pedestrian street protections will help create a more livable, sustainable North Side while addressing our housing needs.",
            created_by="admin",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            jurisdiction_id=jurisdiction_id,
            group_id=group_id,
        )

        # Marcey Street Development
        marcey_development_project = Project(
            id=MARCEY_DEVELOPMENT_PROJECT_ID,
            title="1840 N Marcey Development Support",
            description="Supporting Sterling Bay's proposed mixed-use development at 1840 N Marcey Street in Lincoln Park, which would bring 615 apartments across two towers (25 and 15 stories) to a currently underutilized site near Lincoln Yards.",
            status="active",
            active=True,
            link="https://news.wttw.com/2025/01/09/developer-moves-forward-lincoln-park-apartment-complex-setting-stage-fight-over",
            preferred_status="solid_approval",
            template_response="I support Sterling Bay's proposed development at 1840 N Marcey Street. This project would transform an underutilized site into much-needed housing near jobs and transportation. The 615 apartments would include affordable units and help address Chicago's housing shortage while activating the area with retail spaces and improved pedestrian infrastructure. Density in this location makes sense given its proximity to transit, the Chicago River, and the Lincoln Yards development. I urge you to support this project to bring more housing options and economic activity to the area.",
            created_by="admin",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            jurisdiction_id=jurisdiction_id,
            group_id=group_id,
        )

        # Fern Hill Development
        fern_hill_project = Project(
            id=FERN_HILL_PROJECT_ID,
            title="Old Town Canvas Development Support",
            description="Supporting Fern Hill's proposed Old Town Canvas mixed-use development at North Avenue and LaSalle Drive, which would bring new housing and retail to replace underutilized sites including two gas stations.",
            status="active",
            active=True,
            link="https://www.engagefernhill.com/home",
            preferred_status="solid_approval",
            template_response="I support Fern Hill's Old Town Canvas development project, which would transform underutilized properties at North Avenue and LaSalle Drive into much-needed housing. The project includes affordable units, improved traffic and pedestrian safety features, and will help revitalize a key intersection. The development represents smart urban infill that increases housing supply near jobs and transit while providing community benefits like dedicated Moody Church parking and a grocer in the former Treasure Island space. I urge you to support this project to create a more vibrant, walkable, and housing-rich neighborhood.",
            created_by="admin",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            jurisdiction_id=jurisdiction_id,
            group_id=group_id,
        )

        projects = [
            housing_project,
            two_to_four_flats_project,
            speed_limit_project,
            parking_reform_project,
            vacancy_tax_project,
            broadway_upzoning_project,
            marcey_development_project,
            fern_hill_project,
        ]

        session.add_all(projects)
        await session.commit()

        logger.info(f"Created {len(projects)} Strong Towns Chicago projects")
        return projects
    except SQLAlchemyError as e:
        logger.error(f"Error creating Strong Towns Chicago projects: {str(e)}")
        await session.rollback()
        raise


async def create_random_status_records(session: AsyncSession, entities, projects):
    """Create random status records for aldermen on projects."""
    logger.info("Creating random status records for aldermen...")

    try:
        status_options = [
            "solid_approval",
            "leaning_approval",
            "neutral",
            "leaning_disapproval",
            "solid_disapproval",
        ]
        status_records = []

        for entity in entities:
            for project in projects:
                # Randomly select a status
                status = random.choice(status_options)

                # Random notes based on status
                if status == "solid_approval":
                    notes = f"Strongly supports the {project.title} initiative and has expressed willingness to advocate for it."
                elif status == "leaning_approval":
                    notes = f"Generally supportive of {project.title} but has some questions about implementation details."
                elif status == "neutral":
                    notes = f"Has not taken a clear position on {project.title} and has requested more information."
                elif status == "leaning_disapproval":
                    notes = f"Has expressed some concerns about {project.title} and its potential impacts."
                else:  # solid_disapproval
                    notes = f"Opposes the {project.title} initiative and has publicly stated concerns."

                # Create status record
                record = EntityStatusRecord(
                    id=uuid.uuid4(),
                    entity_id=entity.id,
                    project_id=project.id,
                    status=status,
                    notes=notes,
                    updated_at=datetime.now(timezone.utc),
                    updated_by="admin",
                )

                status_records.append(record)

        session.add_all(status_records)
        await session.commit()
        logger.info(f"Created {len(status_records)} random status records")

        return status_records
    except SQLAlchemyError as e:
        logger.error(f"Error creating random status records: {str(e)}")
        await session.rollback()
        raise


async def main():
    """Main function to run the script."""
    logger.info("Starting Chicago City Council data import...")

    parser = argparse.ArgumentParser(description="Import Chicago City Council data")
    parser.add_argument(
        "--create-tables",
        action="store_true",
        help="Create database tables if they don't exist",
    )
    parser.add_argument(
        "--drop",
        action="store_true",
        help="Drop existing tables before creating new ones (only used with --create-tables)",
    )
    parser.add_argument(
        "--random-statuses",
        action="store_true",
        help="Assign random statuses for aldermen on each project",
    )
    args = parser.parse_args()

    await setup_chicago_city_council_data(
        create_tables=args.create_tables,
        drop_existing=args.drop,
        generate_random_statuses=args.random_statuses,
    )


async def setup_chicago_city_council_data(
    create_tables: bool = True,
    drop_existing: bool = True,
    generate_random_statuses: bool = True,
):
    try:
        # Initialize database
        engine, async_session = await init_db(
            create_tables=create_tables, drop_existing=drop_existing
        )

        # Fetch Chicago aldermen data
        aldermen_data = await fetch_chicago_aldermen()

        if not aldermen_data:
            logger.error("Failed to fetch aldermen data. Exiting.")
            return

        logger.info(f"Successfully fetched {len(aldermen_data)} aldermen records")

        # Create session for database operations
        async with async_session() as session:
            # Create Chicago City Council jurisdiction
            council_jurisdiction_id = await create_chicago_council_jurisdiction(session)

            # Create Strong Towns Chicago group
            group_id = await create_strong_towns_group(session)

            # Create aldermen entities
            entities = await create_aldermen_entities(
                session, aldermen_data, council_jurisdiction_id
            )

            # Create projects for Strong Towns Chicago
            projects = await create_strong_towns_projects(
                session, council_jurisdiction_id, group_id
            )

            # Optionally create random status records
            if generate_random_statuses:
                await create_random_status_records(session, entities, projects)

        # Clean up
        await engine.dispose()

        logger.info("Chicago City Council data import completed successfully!")

    except Exception as e:
        logger.error(f"Chicago data import failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
