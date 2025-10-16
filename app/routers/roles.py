"""Roles router."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.user import User
from app.schemas.role import RoleCreate, RoleResponse, RoleUpdate
from app.schemas.user_role_assignment import UserRoleAssignmentCreate, UserRoleAssignmentResponse
from app.services.role_service import RoleService

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    current_user: User = Depends(require_role(["Admin"])),
    db: AsyncSession = Depends(get_db)
) -> RoleResponse:
    """
    Create a new role (Admin only).

    Args:
        role_data: Role creation data
        current_user: Current authenticated user with Admin role
        db: Database session

    Returns:
        RoleResponse: Created role

    Raises:
        HTTPException: If role name already exists
    """
    try:
        role = await RoleService.create_role(db, role_data)
        return RoleResponse.model_validate(role)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[RoleResponse])
async def get_all_roles(
    current_user: User = Depends(require_role(["Admin"])),
    db: AsyncSession = Depends(get_db)
) -> List[RoleResponse]:
    """
    Get all roles (Admin only).

    Args:
        current_user: Current authenticated user with Admin role
        db: Database session

    Returns:
        List[RoleResponse]: List of roles
    """
    roles = await RoleService.get_all_roles(db)
    return [RoleResponse.model_validate(role) for role in roles]


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: int,
    current_user: User = Depends(require_role(["Admin"])),
    db: AsyncSession = Depends(get_db)
) -> RoleResponse:
    """
    Get role by ID (Admin only).

    Args:
        role_id: Role ID
        current_user: Current authenticated user with Admin role
        db: Database session

    Returns:
        RoleResponse: Role data

    Raises:
        HTTPException: If role not found
    """
    role = await RoleService.get_role_by_id(db, role_id)

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    return RoleResponse.model_validate(role)


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    current_user: User = Depends(require_role(["Admin"])),
    db: AsyncSession = Depends(get_db)
) -> RoleResponse:
    """
    Update role (Admin only).

    Args:
        role_id: Role ID
        role_data: Update data
        current_user: Current authenticated user with Admin role
        db: Database session

    Returns:
        RoleResponse: Updated role

    Raises:
        HTTPException: If role not found
    """
    role = await RoleService.update_role(db, role_id, role_data)

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    return RoleResponse.model_validate(role)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: int,
    current_user: User = Depends(require_role(["Admin"])),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete role (Admin only).

    Args:
        role_id: Role ID
        current_user: Current authenticated user with Admin role
        db: Database session

    Raises:
        HTTPException: If role not found
    """
    success = await RoleService.delete_role(db, role_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )


@router.post("/assignments", response_model=UserRoleAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def assign_role_to_user(
    assignment_data: UserRoleAssignmentCreate,
    current_user: User = Depends(require_role(["Admin"])),
    db: AsyncSession = Depends(get_db)
) -> UserRoleAssignmentResponse:
    """
    Assign a role to a user (Admin only).

    Args:
        assignment_data: Role assignment data
        current_user: Current authenticated user with Admin role
        db: Database session

    Returns:
        UserRoleAssignmentResponse: Created assignment

    Raises:
        HTTPException: If assignment already exists
    """
    try:
        assignment = await RoleService.assign_role_to_user(db, assignment_data)
        return UserRoleAssignmentResponse.model_validate(assignment)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/users/{user_id}/assignments", response_model=List[UserRoleAssignmentResponse])
async def get_user_role_assignments(
    user_id: int,
    current_user: User = Depends(require_role(["Admin"])),
    db: AsyncSession = Depends(get_db)
) -> List[UserRoleAssignmentResponse]:
    """
    Get all role assignments for a user (Admin only).

    Args:
        user_id: User ID
        current_user: Current authenticated user with Admin role
        db: Database session

    Returns:
        List[UserRoleAssignmentResponse]: List of role assignments
    """
    assignments = await RoleService.get_user_roles(db, user_id)
    return [UserRoleAssignmentResponse.model_validate(assignment) for assignment in assignments]
