"""FastAPI dependencies for authentication and authorization."""
from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.models.user_role_assignment import UserRoleAssignment

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer token
        db: Database session

    Returns:
        User: Current authenticated user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user.

    Args:
        current_user: Current authenticated user

    Returns:
        User: Current active user
    """
    return current_user


class RoleChecker:
    """Dependency to check if user has required roles."""

    def __init__(self, required_roles: List[str], hotel_id: Optional[int] = None):
        """
        Initialize role checker.

        Args:
            required_roles: List of required role names
            hotel_id: Optional hotel ID for hotel-scoped role check
        """
        self.required_roles = required_roles
        self.hotel_id = hotel_id

    async def __call__(
        self,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        """
        Check if current user has required roles.

        Args:
            current_user: Current authenticated user
            db: Database session

        Returns:
            User: Current user if authorized

        Raises:
            HTTPException: If user doesn't have required roles
        """
        # Get user's role assignments
        query = select(UserRoleAssignment).where(
            UserRoleAssignment.user_id == current_user.id
        )

        # Filter by hotel_id if specified
        if self.hotel_id is not None:
            query = query.where(
                (UserRoleAssignment.hotel_id == self.hotel_id) |
                (UserRoleAssignment.hotel_id.is_(None))  # Global roles
            )

        result = await db.execute(query)
        role_assignments = result.scalars().all()

        # Get role names
        user_role_names = set()
        for assignment in role_assignments:
            await db.refresh(assignment, ["role"])
            user_role_names.add(assignment.role.name)

        # Check if user has any of the required roles
        if not any(role in user_role_names for role in self.required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )

        return current_user


def require_role(roles: List[str], hotel_id: Optional[int] = None):
    """
    Create a role checker dependency.

    Args:
        roles: List of required role names
        hotel_id: Optional hotel ID for hotel-scoped role check

    Returns:
        RoleChecker: Role checker dependency
    """
    return RoleChecker(required_roles=roles, hotel_id=hotel_id)
