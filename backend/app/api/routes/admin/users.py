from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from typing import List
from pydantic import BaseModel

from app.models.pydantic.models import User, UserRole
from app.services.user_service import UserService
from app.services.service_factory import get_user_service
from app.core.auth import (
    get_group_admin_user,
)

router = APIRouter()


class RoleUpdate(BaseModel):
    role: str


class PasswordUpdate(BaseModel):
    password: str


def _check_edit_permission(
    current_user: User, target_user: User, new_role: UserRole | None = None
) -> None:
    """Raise HTTPException if current_user cannot edit target_user.

    Args:
        current_user: The authenticated user performing the action.
        target_user: The user being modified.
        new_role: The proposed new role (only relevant for role updates).
    """
    if current_user.role == UserRole.SUPER_ADMIN:
        if (
            target_user.role == UserRole.SUPER_ADMIN
            and current_user.id != target_user.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot change the role of another super admin",
            )
    else:  # Group admin
        if target_user.group_id != current_user.group_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only update users in your own group",
            )
        if target_user.role == UserRole.SUPER_ADMIN or new_role == UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Group admins cannot manage super admins",
            )
        if new_role is not None and target_user.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot change your own role",
            )


@router.get("/group/{group_id}", response_model=List[User])
async def list_users_in_group(
    group_id: UUID,
    current_user: User = Depends(get_group_admin_user),
    user_service: UserService = Depends(get_user_service),
):
    """List all users in a group. Only accessible by group admins or super admins."""
    # Super admins can view any group
    # Group admins can only view their own group
    if current_user.role != UserRole.SUPER_ADMIN and current_user.group_id != group_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view users in your own group",
        )

    # Get all users in the group
    users = await user_service.get_users_in_group(group_id)
    return users


@router.patch("/{user_id}/role", response_model=User)
async def update_user_role(
    user_id: UUID,
    role_update: RoleUpdate,
    current_user: User = Depends(get_group_admin_user),
    user_service: UserService = Depends(get_user_service),
):
    """Update a user's role. Only accessible by group admins or super admins."""
    # Check if role is valid
    try:
        new_role = UserRole(role_update.role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join([r.value for r in UserRole])}",
        )

    # Get the user to update
    user_to_update = await user_service.get_user(user_id)
    if not user_to_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    _check_edit_permission(current_user, user_to_update, new_role=new_role)

    # Update the role
    updated_user = await user_service.update_user_role(user_id, new_role)
    return updated_user


@router.patch("/{user_id}/password", response_model=dict)
async def update_user_password(
    user_id: UUID,
    password_update: PasswordUpdate,
    current_user: User = Depends(get_group_admin_user),
    user_service: UserService = Depends(get_user_service),
):
    """Update a user's password. Only accessible by group admins or super admins."""
    # Get the user to update
    user_to_update = await user_service.get_user(user_id)
    if not user_to_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    _check_edit_permission(current_user, user_to_update)

    # Update the password
    await user_service.update_user_password(user_id, password_update.password)
    return {"success": True}
