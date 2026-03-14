from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

from app.models.pydantic.models import User, UserCreate, UserRole
from app.services.service_factory import get_user_service
from app.core.auth import (
    create_access_token,
    get_group_admin_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from app.exceptions import ConflictError, NotFoundError

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/token", summary="Get access token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_service=Depends(get_user_service),
):
    user = await user_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login
    await user_service.update_last_login(user.id)

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role, "group": str(user.group_id)},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=User, summary="Register a new user")
async def register_user(
    user_create: UserCreate,
    current_user: User = Depends(get_group_admin_user),
    user_service=Depends(get_user_service),
):
    # Only allow creating users in the admin's group unless super admin
    if (
        current_user.role != UserRole.SUPER_ADMIN
        and user_create.group_id != current_user.group_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create user in another group",
        )

    try:
        return await user_service.create_user(user_create)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/me", response_model=User, summary="Get current user information")
async def get_user_me(current_user: User = Depends(get_group_admin_user)):
    return current_user
