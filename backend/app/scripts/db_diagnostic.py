import asyncio
import logging
from datetime import datetime
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from typing import Any, Sequence, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("db_diagnostic.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

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
    logger.error(
        "Make sure you're running this script from the correct directory and your models are accessible"
    )
    sys.exit(1)

# Database setup
DATABASE_URL = "sqlite+aiosqlite:///./data/diagnostic_test.db"
logger.info(f"Using database URL: {DATABASE_URL}")


async def init_db() -> Tuple[Any, Any]:
    """Initialize database and return engine and session factory."""
    try:
        engine = create_async_engine(DATABASE_URL, echo=False)
        logger.info("Database engine created")

        # Create database tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            logger.info("Dropped all existing tables")

            await conn.run_sync(Base.metadata.create_all)
            logger.info("Created all tables")

        # Create session factory
        async_session = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        logger.info("Session factory created")

        return engine, async_session
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise


async def create_and_retrieve_jurisdictions(
    session: AsyncSession,
) -> Sequence[Jurisdiction]:
    """Create jurisdictions and verify they can be retrieved."""
    logger.info("=== TESTING JURISDICTIONS ===")

    try:
        # Create test jurisdictions
        jurisdictions = [
            Jurisdiction(
                name="Test City",
                description="A test city jurisdiction",
                level="city",
                created_at=datetime.utcnow(),
            ),
            Jurisdiction(
                name="Test County",
                description="A test county jurisdiction",
                level="county",
                created_at=datetime.utcnow(),
            ),
            Jurisdiction(
                name="Test State",
                description="A test state jurisdiction",
                level="state",
                created_at=datetime.utcnow(),
            ),
        ]

        # Add to database
        session.add_all(jurisdictions)
        await session.commit()
        logger.info(f"Created {len(jurisdictions)} test jurisdictions")

        # Retrieve from database
        result = await session.execute(select(Jurisdiction))
        retrieved_jurisdictions = result.scalars().all()
        logger.info(f"Retrieved {len(retrieved_jurisdictions)} jurisdictions")

        # Log details
        for j in retrieved_jurisdictions:
            logger.info(f"Jurisdiction: id={j.id}, name={j.name}, level={j.level}")

        return retrieved_jurisdictions
    except SQLAlchemyError as e:
        logger.error(f"SQL error in jurisdictions test: {str(e)}")
        await session.rollback()
        return []
    except Exception as e:
        logger.error(f"Unexpected error in jurisdictions test: {str(e)}")
        await session.rollback()
        return []


async def create_and_retrieve_projects(
    session: AsyncSession, jurisdictions: Sequence[Jurisdiction]
) -> Sequence[Project]:
    """Create projects with a direct jurisdiction reference and verify they can be retrieved."""
    logger.info("=== TESTING PROJECTS ===")

    if not jurisdictions:
        logger.warning("No jurisdictions available for project testing")
        return []

    try:
        # Create test projects with direct jurisdiction reference
        projects = [
            Project(
                title="Test Project 1",
                description="A test project for diagnostic purposes",
                status="draft",
                active=True,
                link="https://example.com/test1",
                preferred_status="solid_approval",
                template_response="This is a template response for test project 1",
                created_by="admin",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                jurisdiction_id=jurisdictions[0].id,  # City - direct reference
            ),
            Project(
                title="Test Project 2",
                description="Another test project",
                status="active",
                active=True,
                link="https://example.com/test2",
                preferred_status="neutral",
                template_response="This is a template response for test project 2",
                created_by="admin",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                jurisdiction_id=jurisdictions[2].id,  # State - direct reference
            ),
        ]

        # Add to database
        session.add_all(projects)
        await session.commit()
        logger.info(f"Created {len(projects)} test projects")

        # Retrieve from database
        result = await session.execute(select(Project))
        retrieved_projects = result.scalars().all()
        logger.info(f"Retrieved {len(retrieved_projects)} projects")

        # Log details
        for p in retrieved_projects:
            logger.info(
                f"Project: id={p.id}, title={p.title}, status={p.status}, jurisdiction_id={p.jurisdiction_id}"
            )

        # Test project-jurisdiction relationship
        for project in retrieved_projects:
            jur_result = await session.execute(
                select(Jurisdiction).where(Jurisdiction.id == project.jurisdiction_id)
            )
            jurisdiction = jur_result.scalar_one_or_none()

            if jurisdiction:
                logger.info(
                    f"Project '{project.title}' belongs to jurisdiction '{jurisdiction.name}'"
                )
            else:
                logger.warning(
                    f"Could not find jurisdiction for project '{project.title}'"
                )

        return retrieved_projects
    except SQLAlchemyError as e:
        logger.error(f"SQL error in projects test: {str(e)}")
        await session.rollback()
        return []
    except Exception as e:
        logger.error(f"Unexpected error in projects test: {str(e)}")
        await session.rollback()
        return []


async def create_and_retrieve_entities(
    session: AsyncSession, jurisdictions: Sequence[Jurisdiction]
) -> Sequence[Entity]:
    """Create entities and verify they can be retrieved."""
    logger.info("=== TESTING ENTITIES ===")

    if not jurisdictions:
        logger.warning("No jurisdictions available for entity testing")
        return []

    try:
        # Create test entities
        entities = [
            Entity(
                name="Test Person 1",
                title="Mayor",
                entity_type="mayor",
                jurisdiction_id=jurisdictions[0].id,  # City
                location_module_id="test_city",
                email="mayor@testcity.gov",
                phone="(555) 123-4567",
                website="https://testcity.gov/mayor",
                address="123 Main St, Test City",
            ),
            Entity(
                name="Test Person 2",
                title="Commissioner",
                entity_type="commissioner",
                jurisdiction_id=jurisdictions[1].id,  # County
                location_module_id="test_county",
                email="commissioner@testcounty.gov",
                phone="(555) 765-4321",
                website="https://testcounty.gov/commissioner",
                address="456 County Road, Test County",
            ),
        ]

        # Add to database
        session.add_all(entities)
        await session.commit()
        logger.info(f"Created {len(entities)} test entities")

        # Retrieve from database
        result = await session.execute(select(Entity))
        retrieved_entities = result.scalars().all()
        logger.info(f"Retrieved {len(retrieved_entities)} entities")

        # Log details
        for e in retrieved_entities:
            logger.info(
                f"Entity: id={e.id}, name={e.name}, type={e.entity_type}, jurisdiction_id={e.jurisdiction_id}"
            )
            logger.info(f"  Contact: email={e.email}, phone={e.phone}")

        # Test relationship with jurisdiction
        entity1 = retrieved_entities[0]

        # Get jurisdiction
        ent_jur_result = await session.execute(
            select(Jurisdiction).where(Jurisdiction.id == entity1.jurisdiction_id)
        )
        jurisdiction = ent_jur_result.scalar_one_or_none()

        if jurisdiction:
            logger.info(
                f"Entity '{entity1.name}' belongs to jurisdiction '{jurisdiction.name}'"
            )
        else:
            logger.warning(f"Could not find jurisdiction for entity '{entity1.name}'")

        return retrieved_entities
    except SQLAlchemyError as e:
        logger.error(f"SQL error in entities test: {str(e)}")
        await session.rollback()
        return []
    except Exception as e:
        logger.error(f"Unexpected error in entities test: {str(e)}")
        await session.rollback()
        return []


async def create_and_retrieve_groups(
    session: AsyncSession, projects: Sequence[Project]
) -> Sequence[Group]:
    """Create groups and verify they can be retrieved."""
    logger.info("=== TESTING GROUPS ===")

    if not projects:
        logger.warning("No projects available for group testing")
        return []

    try:
        # Create test groups
        groups = [
            Group(
                name="Test Group 1",
                description="A test group for project 1",
                projects=projects[0],
                created_at=datetime.utcnow(),
            ),
            Group(
                name="Test Group 2",
                description="A test group for project 1",
                projects=projects[0],
                created_at=datetime.utcnow(),
            ),
            Group(
                name="Test Group 3",
                description="A test group for project 2",
                projects=projects[1],
                created_at=datetime.utcnow(),
            ),
        ]

        # Add to database
        session.add_all(groups)
        await session.commit()
        logger.info(f"Created {len(groups)} test groups")

        # Retrieve from database
        result = await session.execute(select(Group))
        retrieved_groups = result.scalars().all()
        logger.info(f"Retrieved {len(retrieved_groups)} groups")

        # Log details
        for g in retrieved_groups:
            logger.info(f"Group: id={g.id}, name={g.name}")

        # Test relationship with project - find projects belonging to the first group
        group1 = retrieved_groups[0]

        # Get projects for this group
        group_proj_result = await session.execute(
            select(Project).where(Project.group_id == group1.id)
        )
        group_project = group_proj_result.scalar_one_or_none()

        if group_project:
            logger.info(f"Group '{group1.name}' has project '{group_project.title}'")
        else:
            logger.warning(f"Could not find project for group '{group1.name}'")

        # Test bidirectional relationship - get projects for a group via project's group_id
        project1 = projects[0]
        proj_group_result = await session.execute(
            select(Project).where(Project.group_id == project1.group_id)
        )
        project_group_projects = proj_group_result.scalars().all()

        logger.info(f"Project '{project1.title}' group has {len(project_group_projects)} projects")
        for p in project_group_projects:
            logger.info(f"  - {p.title}")

        return retrieved_groups
    except SQLAlchemyError as e:
        logger.error(f"SQL error in groups test: {str(e)}")
        await session.rollback()
        return []
    except Exception as e:
        logger.error(f"Unexpected error in groups test: {str(e)}")
        await session.rollback()
        return []


async def create_and_retrieve_status_records(
    session: AsyncSession, entities: Sequence[Entity], projects: Sequence[Project]
) -> Sequence[EntityStatusRecord]:
    """Create entity status records and verify they can be retrieved."""
    logger.info("=== TESTING ENTITY STATUS RECORDS ===")

    if not entities or not projects:
        logger.warning("No entities or projects available for status record testing")
        return []

    try:
        # Create test status records
        status_records = [
            EntityStatusRecord(
                entity_id=entities[0].id,
                project_id=projects[0].id,
                status="solid_approval",
                notes="Test status record 1",
                updated_at=datetime.utcnow(),
                updated_by="admin",
            ),
            EntityStatusRecord(
                entity_id=entities[1].id,
                project_id=projects[0].id,
                status="leaning_disapproval",
                notes="Test status record 2",
                updated_at=datetime.utcnow(),
                updated_by="admin",
            ),
            EntityStatusRecord(
                entity_id=entities[0].id,
                project_id=projects[1].id,
                status="neutral",
                notes="Test status record 3",
                updated_at=datetime.utcnow(),
                updated_by="admin",
            ),
        ]

        # Add to database
        session.add_all(status_records)
        await session.commit()
        logger.info(f"Created {len(status_records)} test status records")

        # Retrieve from database
        result = await session.execute(select(EntityStatusRecord))
        retrieved_records = result.scalars().all()
        logger.info(f"Retrieved {len(retrieved_records)} status records")

        # Log details
        for sr in retrieved_records:
            logger.info(
                f"Status Record: id={sr.id}, entity_id={sr.entity_id}, project_id={sr.project_id}, status={sr.status}"
            )

        # Test relationships
        record1 = retrieved_records[0]

        # Get entity
        ent_result = await session.execute(
            select(Entity).where(Entity.id == record1.entity_id)
        )
        record_entity = ent_result.scalar_one_or_none()

        # Get project
        proj_result = await session.execute(
            select(Project).where(Project.id == record1.project_id)
        )
        record_project = proj_result.scalar_one_or_none()

        if record_entity and record_project:
            logger.info(
                f"Status record shows entity '{record_entity.name}' has status '{record1.status}' for project '{record_project.title}'"
            )
        else:
            logger.warning("Could not find entity or project for status record")

        # Test filtering by project
        filter_result = await session.execute(
            select(EntityStatusRecord).where(
                EntityStatusRecord.project_id == projects[0].id
            )
        )
        project_records = filter_result.scalars().all()

        logger.info(
            f"Project '{projects[0].title}' has {len(project_records)} status records"
        )
        for sr in project_records:
            # Get entity name for better logging
            sr_ent_result = await session.execute(
                select(Entity).where(Entity.id == sr.entity_id)
            )
            sr_entity = sr_ent_result.scalar_one_or_none()
            entity_name = sr_entity.name if sr_entity else "Unknown"

            logger.info(f"  - {entity_name}: {sr.status}")

        return retrieved_records
    except SQLAlchemyError as e:
        logger.error(f"SQL error in status records test: {str(e)}")
        await session.rollback()
        return []
    except Exception as e:
        logger.error(f"Unexpected error in status records test: {str(e)}")
        await session.rollback()
        return []


async def test_updates_and_deletes(
    session: AsyncSession, entities: Sequence[Entity], projects: Sequence[Project]
):
    """Test update and delete operations."""
    logger.info("=== TESTING UPDATES AND DELETES ===")

    if not entities or not projects:
        logger.warning("No entities or projects available for update/delete testing")
        return

    try:
        # Test update
        entity_to_update = entities[0]
        original_name = entity_to_update.name
        new_name = f"{original_name} - UPDATED"

        setattr(entity_to_update, "name", new_name)
        await session.commit()
        logger.info(f"Updated entity name from '{original_name}' to '{new_name}'")

        # Verify update
        update_result = await session.execute(
            select(Entity).where(Entity.id == entity_to_update.id)
        )
        updated_entity = update_result.scalar_one_or_none()

        if updated_entity:
            logger.info(f"Retrieved updated entity: name='{updated_entity.name}'")
            logger.info(f"Update successful: {updated_entity.name == new_name}")
        else:
            logger.warning("Could not retrieve updated entity")

        # Test delete
        project_to_delete = projects[1]
        project_id = project_to_delete.id
        project_title = project_to_delete.title

        await session.delete(project_to_delete)
        await session.commit()
        logger.info(f"Deleted project: {project_title}")

        # Verify delete
        delete_result = await session.execute(select(Project).where(Project.id == project_id))
        deleted_project = delete_result.scalar_one_or_none()

        if deleted_project:
            logger.warning(f"Project was not deleted: {deleted_project.title}")
        else:
            logger.info("Project was successfully deleted")

    except SQLAlchemyError as e:
        logger.error(f"SQL error in update/delete test: {str(e)}")
        await session.rollback()
    except Exception as e:
        logger.error(f"Unexpected error in update/delete test: {str(e)}")
        await session.rollback()


async def test_filtering(
    session: AsyncSession, jurisdictions: Sequence[Jurisdiction], entities: Sequence[Entity]
):
    """Test filtering operations."""
    logger.info("=== TESTING FILTERING ===")

    if not jurisdictions or not entities:
        logger.warning("No jurisdictions or entities available for filtering testing")
        return

    try:
        # Filter entities by jurisdiction
        if jurisdictions and len(jurisdictions) > 0:
            jurisdiction = jurisdictions[0]

            ent_by_jur = await session.execute(
                select(Entity).where(Entity.jurisdiction_id == jurisdiction.id)
            )
            filtered_entities = ent_by_jur.scalars().all()

            logger.info(
                f"Filtered entities by jurisdiction '{jurisdiction.name}': found {len(filtered_entities)}"
            )
            for e in filtered_entities:
                logger.info(f"  - {e.name} (type: {e.entity_type})")

        # Filter entities by entity_type
        if entities and len(entities) > 0:
            entity_type = entities[0].entity_type

            ent_by_type = await session.execute(
                select(Entity).where(Entity.entity_type == entity_type)
            )
            filtered_entities_by_type = ent_by_type.scalars().all()

            logger.info(
                f"Filtered entities by type '{entity_type}': found {len(filtered_entities_by_type)}"
            )
            for e in filtered_entities_by_type:
                logger.info(f"  - {e.name} (jurisdiction_id: {e.jurisdiction_id})")

        # Filter projects by jurisdiction (new test for direct relationship)
        if jurisdictions and len(jurisdictions) > 0:
            jurisdiction = jurisdictions[0]

            proj_by_jur = await session.execute(
                select(Project).where(Project.jurisdiction_id == jurisdiction.id)
            )
            filtered_projects = proj_by_jur.scalars().all()

            logger.info(
                f"Filtered projects by jurisdiction '{jurisdiction.name}': found {len(filtered_projects)}"
            )
            for p in filtered_projects:
                logger.info(f"  - {p.title} (status: {p.status})")

    except SQLAlchemyError as e:
        logger.error(f"SQL error in filtering test: {str(e)}")
        await session.rollback()
    except Exception as e:
        logger.error(f"Unexpected error in filtering test: {str(e)}")
        await session.rollback()


async def main():
    """Run the diagnostic tests."""
    logger.info("Starting database diagnostic tests")

    # Ensure the data directory exists
    os.makedirs("./data", exist_ok=True)

    try:
        # Initialize the database
        engine, async_session = await init_db()

        # Create a new session for testing
        async with async_session() as session:
            # Run tests
            jurisdictions = await create_and_retrieve_jurisdictions(session)
            projects = await create_and_retrieve_projects(session, jurisdictions)
            entities = await create_and_retrieve_entities(session, jurisdictions)
            _ = await create_and_retrieve_groups(session, projects)
            _ = await create_and_retrieve_status_records(session, entities, projects)

            # Additional tests
            await test_updates_and_deletes(session, entities, projects)
            await test_filtering(session, jurisdictions, entities)

        # Clean up
        await engine.dispose()

        logger.info("Database diagnostic tests completed")

    except Exception as e:
        logger.error(f"An error occurred during testing: {str(e)}")
        logger.error("Diagnostic tests failed")


if __name__ == "__main__":
    asyncio.run(main())
