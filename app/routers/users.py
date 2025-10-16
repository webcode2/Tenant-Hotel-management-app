"""Users router."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_role
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> UserResponse:
    """
    Get current user information.

    Args:
        current_user: Current authenticated user

    Returns:
        UserResponse: Current user data
    """
    return UserResponse.model_validate(current_user)


@router.get("/", response_model=List[UserResponse])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_role(["Admin"])),
    db: AsyncSession = Depends(get_db)
) -> List[UserResponse]:
    """
    Get all users (Admin only).

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Current authenticated user with Admin role
        db: Database session

    Returns:
        List[UserResponse]: List of users
    """
    users = await UserService.get_all_users(db, skip, limit)
    return [UserResponse.model_validate(user) for user in users]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(require_role(["Admin"])),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Get user by ID (Admin only).

    Args:
        user_id: User ID
        current_user: Current authenticated user with Admin role
        db: Database session

    Returns:
        UserResponse: User data

    Raises:
        HTTPException: If user not found
    """
    user = await UserService.get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Update user (own profile or Admin).

    Args:
        user_id: User ID
        user_data: Update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        UserResponse: Updated user

    Raises:
        HTTPException: If user not found or not authorized
    """
    # Check if user is updating their own profile or is an admin
    if current_user.id != user_id:
        # Check if user has Admin role
        from app.services.role_service import RoleService
        assignments = await RoleService.get_user_roles(db, current_user.id)
        is_admin = any(
            assignment.role.name == "Admin" and assignment.hotel_id is None
            for assignment in assignments
        )

        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )

    user = await UserService.update_user(db, user_id, user_data)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_role(["Admin"])),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete user (Admin only).

    Args:
        user_id: User ID
        current_user: Current authenticated user with Admin role
        db: Database session

    Raises:
        HTTPException: If user not found
    """
    success = await UserService.delete_user(db, user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
