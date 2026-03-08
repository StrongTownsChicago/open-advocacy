"""Shared pytest fixtures."""

import pytest

from tests.mock_provider import MockDatabaseProvider
from app.services.project_service import ProjectService
from app.services.status_service import StatusService
from app.services.user_service import UserService


@pytest.fixture
def mock_provider() -> MockDatabaseProvider:
    return MockDatabaseProvider()


@pytest.fixture
def project_service() -> ProjectService:
    return ProjectService(
        projects_provider=MockDatabaseProvider(),
        status_records_provider=MockDatabaseProvider(),
        entities_provider=MockDatabaseProvider(),
        jurisdictions_provider=MockDatabaseProvider(),
        groups_provider=MockDatabaseProvider(),
    )


@pytest.fixture
def status_service() -> StatusService:
    return StatusService(
        status_records_provider=MockDatabaseProvider(),
        projects_provider=MockDatabaseProvider(),
        entities_provider=MockDatabaseProvider(),
    )


@pytest.fixture
def user_service() -> UserService:
    return UserService(
        users_provider=MockDatabaseProvider(),
        groups_provider=MockDatabaseProvider(),
    )
