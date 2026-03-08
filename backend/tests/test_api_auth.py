"""Tests for auth API route integration (login, register, permissions)."""

from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.auth import create_access_token, get_password_hash
from app.main import app
from app.models.pydantic.models import UserRole
from app.services.service_factory import get_user_service
from tests.factories import make_group, make_user
from tests.mock_provider import MockDatabaseProvider

TEST_SECRET_KEY = "test-secret-key-for-api-tests"


def _build_user_service():
    """Create a UserService backed by mock providers with a seeded user."""
    from app.services.user_service import UserService

    users_provider = MockDatabaseProvider()
    groups_provider = MockDatabaseProvider()

    group = make_group(name="Test Group")
    groups_provider.seed(group)

    hashed = get_password_hash("correctpassword")
    user = make_user(
        email="admin@test.com",
        name="Admin",
        group_id=group.id,
        role=UserRole.SUPER_ADMIN,
        hashed_password=hashed,
    )
    users_provider.seed(user)

    service = UserService(
        users_provider=users_provider,
        groups_provider=groups_provider,
    )
    return service, user, group


class TestAuthEndpoints:
    """Test login and register routes through the FastAPI app."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.service, self.user, self.group = _build_user_service()
        app.dependency_overrides[get_user_service] = lambda: self.service
        yield
        app.dependency_overrides.clear()

    @patch("app.core.auth.SECRET_KEY", TEST_SECRET_KEY)
    async def test_login_valid_credentials_returns_token(self):
        """POST /api/auth/token with correct credentials returns access_token."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/auth/token",
                data={"username": "admin@test.com", "password": "correctpassword"},
            )
        assert response.status_code == 200
        body = response.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    @patch("app.core.auth.SECRET_KEY", TEST_SECRET_KEY)
    async def test_login_invalid_credentials_returns_401(self):
        """POST /api/auth/token with wrong password returns 401."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/auth/token",
                data={"username": "admin@test.com", "password": "wrongpassword"},
            )
        assert response.status_code == 401

    async def test_register_without_auth_returns_401(self):
        """POST /api/auth/register without a token returns 401."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/auth/register",
                json={
                    "email": "new@test.com",
                    "name": "New User",
                    "password": "password123",
                    "group_id": str(self.group.id),
                    "role": "viewer",
                },
            )
        assert response.status_code == 401

    @patch("app.core.auth.SECRET_KEY", TEST_SECRET_KEY)
    async def test_register_group_admin_cross_group_returns_403(self):
        """A group_admin creating a user in a different group should get 403."""
        # Create a group_admin user
        hashed = get_password_hash("gadminpass")
        other_group = make_group(name="Other Group")
        self.service.groups_provider.seed(other_group)

        group_admin = make_user(
            email="gadmin@test.com",
            name="Group Admin",
            group_id=self.group.id,
            role=UserRole.GROUP_ADMIN,
            hashed_password=hashed,
        )
        self.service.users_provider.seed(group_admin)

        # Override get_current_user to return our group_admin directly
        from app.core.auth import get_current_user

        async def mock_get_current_user():
            return group_admin

        app.dependency_overrides[get_current_user] = mock_get_current_user

        # Create a token (needed for the Authorization header, even though we override get_current_user)
        token = create_access_token(
            data={
                "sub": str(group_admin.id),
                "role": group_admin.role,
                "group": str(group_admin.group_id),
            }
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/auth/register",
                json={
                    "email": "cross@test.com",
                    "name": "Cross Group User",
                    "password": "password123",
                    "group_id": str(other_group.id),
                    "role": "viewer",
                },
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 403
        assert "Cannot create user in another group" in response.json()["detail"]
