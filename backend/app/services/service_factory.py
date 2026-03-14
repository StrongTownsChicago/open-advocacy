from fastapi import Depends
from functools import lru_cache

from app.db.dependencies import (
    get_projects_provider,
    get_groups_provider,
    get_entities_provider,
    get_status_records_provider,
    get_jurisdictions_provider,
    get_districts_provider,
    get_users_provider,
)
from app.services.project_service import ProjectService
from app.services.entity_service import EntityService
from app.services.jurisdiction_service import JurisdictionService
from app.services.status_service import StatusService
from app.services.district_service import DistrictService
from app.services.group_service import GroupService
from app.services.user_service import UserService
from app.services.scorecard_service import ScorecardService
from app.geo.provider_factory import get_geo_provider


# Service factory implementations without FastAPI dependency (so we can use with scripts as well)
def create_project_service(
    projects_provider=None,
    status_records_provider=None,
    entities_provider=None,
    jurisdictions_provider=None,
    groups_provider=None,
) -> ProjectService:
    """Create a ProjectService instance."""
    return ProjectService(
        projects_provider=projects_provider or get_projects_provider(),
        status_records_provider=status_records_provider
        or get_status_records_provider(),
        entities_provider=entities_provider or get_entities_provider(),
        jurisdictions_provider=jurisdictions_provider or get_jurisdictions_provider(),
        groups_provider=groups_provider or get_groups_provider(),
    )


def create_entity_service(
    entities_provider=None,
    jurisdictions_provider=None,
    districts_provider=None,
    geo_provider=None,
) -> EntityService:
    """Create an EntityService instance."""
    return EntityService(
        entities_provider=entities_provider or get_entities_provider(),
        jurisdictions_provider=jurisdictions_provider or get_jurisdictions_provider(),
        districts_provider=districts_provider or get_districts_provider(),
        geo_provider=geo_provider or get_geo_provider(),
    )


def create_jurisdiction_service(
    jurisdictions_provider=None,
) -> JurisdictionService:
    """Create a JurisdictionService instance."""
    return JurisdictionService(
        jurisdictions_provider=jurisdictions_provider or get_jurisdictions_provider(),
    )


def create_status_service(
    status_records_provider=None,
    projects_provider=None,
    entities_provider=None,
) -> StatusService:
    """Create a StatusService instance."""
    return StatusService(
        status_records_provider=status_records_provider
        or get_status_records_provider(),
        projects_provider=projects_provider or get_projects_provider(),
        entities_provider=entities_provider or get_entities_provider(),
    )


def create_district_service(
    districts_provider=None,
    jurisdictions_provider=None,
) -> DistrictService:
    """Create a DistrictService instance."""
    return DistrictService(
        districts_provider=districts_provider or get_districts_provider(),
        jurisdictions_provider=jurisdictions_provider or get_jurisdictions_provider(),
    )


def create_group_service(groups_provider=None):
    """Create a GroupService instance."""
    return GroupService(groups_provider=groups_provider or get_groups_provider())


def create_user_service(
    users_provider=None,
    groups_provider=None,
) -> UserService:
    """Create a UserService instance."""
    return UserService(
        users_provider=users_provider or get_users_provider(),
        groups_provider=groups_provider or get_groups_provider(),
    )


def create_scorecard_service(
    projects_provider=None,
    entities_provider=None,
    status_records_provider=None,
    districts_provider=None,
) -> ScorecardService:
    """Create a ScorecardService instance."""
    return ScorecardService(
        projects_provider=projects_provider or get_projects_provider(),
        entities_provider=entities_provider or get_entities_provider(),
        status_records_provider=status_records_provider
        or get_status_records_provider(),
        districts_provider=districts_provider or get_districts_provider(),
    )


# FastAPI dependency functions that can be used with Depends()
def get_project_service(
    projects_provider=Depends(get_projects_provider),
    status_records_provider=Depends(get_status_records_provider),
    entities_provider=Depends(get_entities_provider),
    jurisdictions_provider=Depends(get_jurisdictions_provider),
    groups_provider=Depends(get_groups_provider),
) -> ProjectService:
    """Get a ProjectService instance with dependencies injected."""
    return ProjectService(
        projects_provider=projects_provider,
        status_records_provider=status_records_provider,
        entities_provider=entities_provider,
        jurisdictions_provider=jurisdictions_provider,
        groups_provider=groups_provider,
    )


def get_entity_service(
    entities_provider=Depends(get_entities_provider),
    jurisdictions_provider=Depends(get_jurisdictions_provider),
    districts_provider=Depends(get_districts_provider),
) -> EntityService:
    """Get an EntityService instance with dependencies injected."""
    return EntityService(
        entities_provider=entities_provider,
        jurisdictions_provider=jurisdictions_provider,
        districts_provider=districts_provider,
        geo_provider=get_geo_provider(),
    )


def get_jurisdiction_service(
    jurisdictions_provider=Depends(get_jurisdictions_provider),
) -> JurisdictionService:
    """Get a JurisdictionService instance with dependencies injected."""
    return JurisdictionService(
        jurisdictions_provider=jurisdictions_provider,
    )


def get_status_service(
    status_records_provider=Depends(get_status_records_provider),
    projects_provider=Depends(get_projects_provider),
    entities_provider=Depends(get_entities_provider),
) -> StatusService:
    """Get a StatusService instance with dependencies injected."""
    return StatusService(
        status_records_provider=status_records_provider,
        projects_provider=projects_provider,
        entities_provider=entities_provider,
    )


def get_district_service(
    districts_provider=Depends(get_districts_provider),
    jurisdictions_provider=Depends(get_jurisdictions_provider),
) -> DistrictService:
    """Get a DistrictService instance with dependencies injected."""
    return DistrictService(
        districts_provider=districts_provider,
        jurisdictions_provider=jurisdictions_provider,
    )


def get_group_service(groups_provider=Depends(get_groups_provider)):
    """Dependency to get the group service."""
    return GroupService(groups_provider=groups_provider)


def get_user_service(
    users_provider=Depends(get_users_provider),
    groups_provider=Depends(get_groups_provider),
) -> UserService:
    """Get a UserService instance with dependencies injected."""
    return UserService(
        users_provider=users_provider,
        groups_provider=groups_provider,
    )


def get_scorecard_service(
    projects_provider=Depends(get_projects_provider),
    entities_provider=Depends(get_entities_provider),
    status_records_provider=Depends(get_status_records_provider),
    districts_provider=Depends(get_districts_provider),
) -> ScorecardService:
    """Get a ScorecardService instance with dependencies injected."""
    return ScorecardService(
        projects_provider=projects_provider,
        entities_provider=entities_provider,
        status_records_provider=status_records_provider,
        districts_provider=districts_provider,
    )


# Cached singleton versions for script usage to avoid recreating the same service objects repeatedly
@lru_cache()
def get_cached_project_service() -> ProjectService:
    """Get a cached singleton ProjectService instance."""
    return create_project_service()


@lru_cache()
def get_cached_entity_service() -> EntityService:
    """Get a cached singleton EntityService instance."""
    return create_entity_service()


@lru_cache()
def get_cached_jurisdiction_service() -> JurisdictionService:
    """Get a cached singleton JurisdictionService instance."""
    return create_jurisdiction_service()


@lru_cache()
def get_cached_status_service() -> StatusService:
    """Get a cached singleton StatusService instance."""
    return create_status_service()


@lru_cache()
def get_cached_district_service() -> DistrictService:
    """Get a cached singleton DistrictService instance."""
    return create_district_service()


@lru_cache()
def get_cached_group_service() -> GroupService:
    """Get a cached singleton GroupService instance."""
    return create_group_service()


@lru_cache()
def get_cached_user_service() -> UserService:
    """Get a cached singleton UserService instance."""
    return create_user_service()
