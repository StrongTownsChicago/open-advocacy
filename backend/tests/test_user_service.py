"""Tests for UserService: creation, validation, authentication."""

from uuid import uuid4

import pytest

from app.core.auth import get_password_hash
from app.models.pydantic.models import UserCreate, UserRole
from app.services.user_service import UserService
from tests.factories import make_group, make_user
from tests.mock_provider import MockDatabaseProvider


class TestCreateUser:
    """Tests for user creation with validation."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.users_provider = MockDatabaseProvider()
        self.groups_provider = MockDatabaseProvider()
        self.service = UserService(
            users_provider=self.users_provider,
            groups_provider=self.groups_provider,
        )

    async def test_create_user_hashes_password(self):
        """Created user should have a hashed password, not the plain text."""
        group = make_group()
        self.groups_provider.seed(group)

        user_create = UserCreate(
            email="new@example.com",
            name="New User",
            password="plain_password",
            group_id=group.id,
            role=UserRole.VIEWER,
        )
        result = await self.service.create_user(user_create)
        # The result is a dict from MockDatabaseProvider
        assert isinstance(result, dict)
        assert result["hashed_password"] != "plain_password"
        assert "password" not in result

    async def test_create_user_validates_group(self):
        """Creating a user with nonexistent group should raise ValueError."""
        user_create = UserCreate(
            email="new@example.com",
            name="New User",
            password="password",
            group_id=uuid4(),
            role=UserRole.VIEWER,
        )
        with pytest.raises(ValueError, match="Group not found"):
            await self.service.create_user(user_create)

    async def test_create_user_rejects_duplicate_email(self):
        """Creating a user with an existing email should raise ValueError."""
        group = make_group()
        self.groups_provider.seed(group)

        existing_user = make_user(email="taken@example.com", group_id=group.id)
        self.users_provider.seed(existing_user)

        user_create = UserCreate(
            email="taken@example.com",
            name="Duplicate",
            password="password",
            group_id=group.id,
            role=UserRole.VIEWER,
        )
        with pytest.raises(ValueError, match="Email already registered"):
            await self.service.create_user(user_create)


class TestAuthenticateUser:
    """Tests for user authentication."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.users_provider = MockDatabaseProvider()
        self.groups_provider = MockDatabaseProvider()
        self.service = UserService(
            users_provider=self.users_provider,
            groups_provider=self.groups_provider,
        )

    async def test_authenticate_correct_credentials(self):
        """Correct email and password should return the user."""
        hashed = get_password_hash("correct_password")
        user = make_user(email="auth@example.com", hashed_password=hashed)
        self.users_provider.seed(user)

        result = await self.service.authenticate_user(
            "auth@example.com", "correct_password"
        )
        assert result is not None
        assert result.email == "auth@example.com"

    async def test_authenticate_wrong_password(self):
        """Wrong password should return None."""
        hashed = get_password_hash("correct_password")
        user = make_user(email="auth@example.com", hashed_password=hashed)
        self.users_provider.seed(user)

        result = await self.service.authenticate_user(
            "auth@example.com", "wrong_password"
        )
        assert result is None

    async def test_authenticate_missing_user(self):
        """Authenticating with nonexistent email should return None."""
        result = await self.service.authenticate_user(
            "nonexistent@example.com", "password"
        )
        assert result is None
