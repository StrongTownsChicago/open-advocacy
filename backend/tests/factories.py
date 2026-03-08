"""Test data factories for creating model instances."""

from datetime import datetime
from uuid import UUID, uuid4

from app.models.pydantic.models import (
    Entity,
    EntityStatus,
    EntityStatusRecord,
    Group,
    Jurisdiction,
    Project,
    ProjectStatus,
    User,
    UserRole,
)


def make_group(
    id: UUID | None = None,
    name: str = "Test Group",
    description: str = "A test group",
    is_public: bool = True,
) -> Group:
    return Group(
        id=id or uuid4(),
        name=name,
        description=description,
        is_public=is_public,
        created_at=datetime.now(),
    )


def make_jurisdiction(
    id: UUID | None = None,
    name: str = "Test Jurisdiction",
    description: str = "A test jurisdiction",
    level: str = "city",
) -> Jurisdiction:
    return Jurisdiction(
        id=id or uuid4(),
        name=name,
        description=description,
        level=level,
        created_at=datetime.now(),
    )


def make_project(
    id: UUID | None = None,
    title: str = "Test Project",
    description: str = "A test project",
    status: ProjectStatus = ProjectStatus.ACTIVE,
    jurisdiction_id: UUID | None = None,
    group_id: UUID | None = None,
    preferred_status: EntityStatus = EntityStatus.SOLID_APPROVAL,
) -> Project:
    return Project(
        id=id or uuid4(),
        title=title,
        description=description,
        status=status,
        active=True,
        preferred_status=preferred_status,
        jurisdiction_id=jurisdiction_id or uuid4(),
        group_id=group_id or uuid4(),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


def make_entity(
    id: UUID | None = None,
    name: str = "Test Entity",
    entity_type: str = "alderman",
    jurisdiction_id: UUID | None = None,
    district_id: UUID | None = None,
) -> Entity:
    return Entity(
        id=id or uuid4(),
        name=name,
        entity_type=entity_type,
        jurisdiction_id=jurisdiction_id or uuid4(),
        district_id=district_id or uuid4(),
    )


def make_status_record(
    id: UUID | None = None,
    entity_id: UUID | None = None,
    project_id: UUID | None = None,
    status: EntityStatus = EntityStatus.UNKNOWN,
    updated_by: str = "test_user",
) -> EntityStatusRecord:
    return EntityStatusRecord(
        id=id or uuid4(),
        entity_id=entity_id or uuid4(),
        project_id=project_id or uuid4(),
        status=status,
        updated_by=updated_by,
        updated_at=datetime.now(),
    )


def make_district(
    id: UUID | None = None,
    name: str = "Test District",
    code: str | None = None,
    jurisdiction_id: UUID | None = None,
):
    from app.models.pydantic.models import District

    return District(
        id=id or uuid4(),
        name=name,
        code=code,
        jurisdiction_id=jurisdiction_id or uuid4(),
    )


def make_user(
    id: UUID | None = None,
    email: str = "test@example.com",
    name: str = "Test User",
    group_id: UUID | None = None,
    role: str = UserRole.VIEWER,
    hashed_password: str = "hashed_pw",
    is_active: bool = True,
) -> User:
    return User(
        id=id or uuid4(),
        email=email,
        name=name,
        group_id=group_id or uuid4(),
        role=role,
        hashed_password=hashed_password,
        is_active=is_active,
        created_at=datetime.now(),
    )
