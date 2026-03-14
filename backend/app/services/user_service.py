from uuid import UUID
from datetime import datetime

from app.models.pydantic.models import User, UserCreate, UserRole
from app.core.auth import get_password_hash, verify_password
from app.db.base import DatabaseProvider
from app.exceptions import ConflictError, NotFoundError


class UserService:
    def __init__(
        self, users_provider: DatabaseProvider, groups_provider: DatabaseProvider
    ):
        self.users_provider = users_provider
        self.groups_provider = groups_provider

    async def get_user(self, user_id: UUID) -> User | None:
        """Get a user by ID."""
        return await self.users_provider.get(user_id)

    async def get_user_by_email(self, email: str) -> User | None:
        """Get a user by email."""
        users = await self.users_provider.filter(email=email)
        return users[0] if users else None

    async def authenticate_user(self, email: str, password: str) -> User | None:
        """Authenticate a user by email and password."""
        user = await self.get_user_by_email(email)
        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return user

    async def create_user(self, user_create: UserCreate) -> User:
        """Create a new user."""
        # Verify group exists
        group = await self.groups_provider.get(user_create.group_id)
        if not group:
            raise NotFoundError("Group not found")

        # Check if email already exists
        existing = await self.get_user_by_email(user_create.email)
        if existing:
            raise ConflictError("Email already registered")

        # Create user with hashed password
        user_data = user_create.model_dump(exclude={"password"})
        user_data["hashed_password"] = get_password_hash(user_create.password)

        return await self.users_provider.create(user_data)

    async def update_last_login(self, user_id: UUID) -> None:
        """Update the last login timestamp for a user."""
        await self.users_provider.update(user_id, {"last_login": datetime.utcnow()})

    async def get_users_in_group(self, group_id: UUID) -> list[User]:
        """Get all users in a group."""
        return await self.users_provider.filter(group_id=group_id)

    async def update_user_role(self, user_id: UUID, new_role: UserRole) -> User:
        """Update a user's role."""
        updated_user = await self.users_provider.update(user_id, {"role": new_role})
        if updated_user is None:
            raise NotFoundError("User not found")
        return updated_user

    async def update_user_password(self, user_id: UUID, new_password: str) -> bool:
        """Update a user's password."""
        hashed_password = get_password_hash(new_password)
        await self.users_provider.update(user_id, {"hashed_password": hashed_password})
        return True
