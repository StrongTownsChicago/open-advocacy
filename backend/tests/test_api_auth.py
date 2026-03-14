"""Tests for auth API route integration (login, register, permissions)."""

from unittest.mock import patch
from uuid import uuid4

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


class TestAdminRoleUpdatePermissions:
    """Tests for the complex permission logic in admin/users role update endpoint."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from app.core.auth import get_group_admin_user

        self.service, self.super_admin, self.group = _build_user_service()
        app.dependency_overrides[get_user_service] = lambda: self.service
        self._get_group_admin_user = get_group_admin_user
        yield
        app.dependency_overrides.clear()

    def _setup_user_override(self, user):
        """Override get_group_admin_user to return the given user."""

        async def mock_get_admin():
            return user

        app.dependency_overrides[self._get_group_admin_user] = mock_get_admin

    @patch("app.core.auth.SECRET_KEY", TEST_SECRET_KEY)
    async def test_super_admin_cannot_change_other_super_admin_role(self):
        """A super admin cannot change another super admin's role."""
        other_super = make_user(
            email="other_super@test.com",
            name="Other Super",
            group_id=self.group.id,
            role=UserRole.SUPER_ADMIN,
            hashed_password=get_password_hash("pass"),
        )
        self.service.users_provider.seed(other_super)
        self._setup_user_override(self.super_admin)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                f"/api/users/{other_super.id}/role",
                json={"role": "editor"},
                headers={"Authorization": "Bearer fake"},
            )
        assert response.status_code == 403
        assert "another super admin" in response.json()["detail"]

    @patch("app.core.auth.SECRET_KEY", TEST_SECRET_KEY)
    async def test_group_admin_cannot_elevate_to_super_admin(self):
        """A group admin cannot elevate a user to super_admin."""
        group_admin = make_user(
            email="gadmin@test.com",
            name="Group Admin",
            group_id=self.group.id,
            role=UserRole.GROUP_ADMIN,
            hashed_password=get_password_hash("pass"),
        )
        self.service.users_provider.seed(group_admin)

        target_user = make_user(
            email="target@test.com",
            name="Target",
            group_id=self.group.id,
            role=UserRole.EDITOR,
            hashed_password=get_password_hash("pass"),
        )
        self.service.users_provider.seed(target_user)
        self._setup_user_override(group_admin)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                f"/api/users/{target_user.id}/role",
                json={"role": "super_admin"},
                headers={"Authorization": "Bearer fake"},
            )
        assert response.status_code == 403
        assert "cannot manage super admins" in response.json()["detail"].lower()

    @patch("app.core.auth.SECRET_KEY", TEST_SECRET_KEY)
    async def test_group_admin_cannot_change_own_role(self):
        """A group admin cannot change their own role."""
        group_admin = make_user(
            email="gadmin2@test.com",
            name="Group Admin 2",
            group_id=self.group.id,
            role=UserRole.GROUP_ADMIN,
            hashed_password=get_password_hash("pass"),
        )
        self.service.users_provider.seed(group_admin)
        self._setup_user_override(group_admin)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                f"/api/users/{group_admin.id}/role",
                json={"role": "editor"},
                headers={"Authorization": "Bearer fake"},
            )
        assert response.status_code == 403
        assert "Cannot change your own role" in response.json()["detail"]

    @patch("app.core.auth.SECRET_KEY", TEST_SECRET_KEY)
    async def test_group_admin_cannot_modify_other_group_user(self):
        """A group admin can only modify users in their own group."""
        other_group = make_group(name="Other Group")
        self.service.groups_provider.seed(other_group)

        group_admin = make_user(
            email="gadmin3@test.com",
            name="Group Admin 3",
            group_id=self.group.id,
            role=UserRole.GROUP_ADMIN,
            hashed_password=get_password_hash("pass"),
        )
        self.service.users_provider.seed(group_admin)

        other_user = make_user(
            email="other@test.com",
            name="Other User",
            group_id=other_group.id,
            role=UserRole.EDITOR,
            hashed_password=get_password_hash("pass"),
        )
        self.service.users_provider.seed(other_user)
        self._setup_user_override(group_admin)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                f"/api/users/{other_user.id}/role",
                json={"role": "viewer"},
                headers={"Authorization": "Bearer fake"},
            )
        assert response.status_code == 403
        assert "your own group" in response.json()["detail"]

    @patch("app.core.auth.SECRET_KEY", TEST_SECRET_KEY)
    async def test_super_admin_can_change_non_super_admin_role(self):
        """A super admin can change any non-super-admin user's role."""
        target_user = make_user(
            email="target2@test.com",
            name="Target 2",
            group_id=self.group.id,
            role=UserRole.EDITOR,
            hashed_password=get_password_hash("pass"),
        )
        self.service.users_provider.seed(target_user)
        self._setup_user_override(self.super_admin)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                f"/api/users/{target_user.id}/role",
                json={"role": "group_admin"},
                headers={"Authorization": "Bearer fake"},
            )
        assert response.status_code == 200
        assert response.json()["role"] == "group_admin"


class TestAdminPasswordEndpoint:
    """Tests for the PATCH /api/users/{user_id}/password permission logic."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from app.core.auth import get_group_admin_user

        self.service, self.super_admin, self.group = _build_user_service()
        app.dependency_overrides[get_user_service] = lambda: self.service
        self._get_group_admin_user = get_group_admin_user
        yield
        app.dependency_overrides.clear()

    def _setup_user_override(self, user):
        async def mock_get_admin():
            return user

        app.dependency_overrides[self._get_group_admin_user] = mock_get_admin

    @patch("app.core.auth.SECRET_KEY", TEST_SECRET_KEY)
    async def test_update_password_requires_auth(self):
        """PATCH without token → 401."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                f"/api/users/{uuid4()}/password",
                json={"password": "newpass"},
            )
        assert response.status_code == 401

    @patch("app.core.auth.SECRET_KEY", TEST_SECRET_KEY)
    async def test_super_admin_updates_editor_password(self):
        """Super admin can update an editor's password → 200."""
        editor = make_user(
            email="editor@test.com",
            name="Editor",
            group_id=self.group.id,
            role=UserRole.EDITOR,
            hashed_password=get_password_hash("pass"),
        )
        self.service.users_provider.seed(editor)
        self._setup_user_override(self.super_admin)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                f"/api/users/{editor.id}/password",
                json={"password": "newpassword"},
                headers={"Authorization": "Bearer fake"},
            )
        assert response.status_code == 200

    @patch("app.core.auth.SECRET_KEY", TEST_SECRET_KEY)
    async def test_super_admin_cannot_update_other_super_admin(self):
        """Super admin cannot update another super admin's password → 403."""
        other_super = make_user(
            email="other_super@test.com",
            name="Other Super",
            group_id=self.group.id,
            role=UserRole.SUPER_ADMIN,
            hashed_password=get_password_hash("pass"),
        )
        self.service.users_provider.seed(other_super)
        self._setup_user_override(self.super_admin)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                f"/api/users/{other_super.id}/password",
                json={"password": "newpassword"},
                headers={"Authorization": "Bearer fake"},
            )
        assert response.status_code == 403

    @patch("app.core.auth.SECRET_KEY", TEST_SECRET_KEY)
    async def test_group_admin_updates_user_in_own_group(self):
        """Group admin can update a user's password in their own group → 200."""
        group_admin = make_user(
            email="gadmin@test.com",
            name="Group Admin",
            group_id=self.group.id,
            role=UserRole.GROUP_ADMIN,
            hashed_password=get_password_hash("pass"),
        )
        editor = make_user(
            email="editor2@test.com",
            name="Editor 2",
            group_id=self.group.id,
            role=UserRole.EDITOR,
            hashed_password=get_password_hash("pass"),
        )
        self.service.users_provider.seed(group_admin)
        self.service.users_provider.seed(editor)
        self._setup_user_override(group_admin)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                f"/api/users/{editor.id}/password",
                json={"password": "newpassword"},
                headers={"Authorization": "Bearer fake"},
            )
        assert response.status_code == 200

    @patch("app.core.auth.SECRET_KEY", TEST_SECRET_KEY)
    async def test_group_admin_cannot_update_other_group(self):
        """Group admin cannot update a user in a different group → 403."""
        other_group = make_group(name="Other Group")
        self.service.groups_provider.seed(other_group)

        group_admin = make_user(
            email="gadmin2@test.com",
            name="Group Admin 2",
            group_id=self.group.id,
            role=UserRole.GROUP_ADMIN,
            hashed_password=get_password_hash("pass"),
        )
        other_user = make_user(
            email="other@test.com",
            name="Other User",
            group_id=other_group.id,
            role=UserRole.EDITOR,
            hashed_password=get_password_hash("pass"),
        )
        self.service.users_provider.seed(group_admin)
        self.service.users_provider.seed(other_user)
        self._setup_user_override(group_admin)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                f"/api/users/{other_user.id}/password",
                json={"password": "newpassword"},
                headers={"Authorization": "Bearer fake"},
            )
        assert response.status_code == 403

    @patch("app.core.auth.SECRET_KEY", TEST_SECRET_KEY)
    async def test_group_admin_cannot_update_super_admin(self):
        """Group admin cannot update a super admin's password → 403."""
        group_admin = make_user(
            email="gadmin3@test.com",
            name="Group Admin 3",
            group_id=self.group.id,
            role=UserRole.GROUP_ADMIN,
            hashed_password=get_password_hash("pass"),
        )
        self.service.users_provider.seed(group_admin)
        self._setup_user_override(group_admin)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                f"/api/users/{self.super_admin.id}/password",
                json={"password": "newpassword"},
                headers={"Authorization": "Bearer fake"},
            )
        assert response.status_code == 403

    @patch("app.core.auth.SECRET_KEY", TEST_SECRET_KEY)
    async def test_update_password_user_not_found(self):
        """Super admin with random UUID → 404."""
        self._setup_user_override(self.super_admin)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                f"/api/users/{uuid4()}/password",
                json={"password": "newpassword"},
                headers={"Authorization": "Bearer fake"},
            )
        assert response.status_code == 404
