"""User service."""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.account_module.models.user import User
from app.account_module.schemas.user import UserUpdate
from app.core.security import get_password_hash


class UserService:
    """Service for user operations."""

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """
        Get user by ID.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Optional[User]: User or None if not found
        """
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """
        Get user by email.

        Args:
            db: Database session
            email: User email

        Returns:
            Optional[User]: User or None if not found
        """
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get all users with pagination.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List[User]: List of users
        """
        result = await db.execute(select(User).offset(skip).limit(limit))
        return list(result.scalars().all())

    @staticmethod
    async def update_user(db: AsyncSession, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """
        Update user.

        Args:
            db: Database session
            user_id: User ID
            user_data: Update data

        Returns:
            Optional[User]: Updated user or None if not found
        """
        user = await UserService.get_user_by_id(db, user_id)

        if not user:
            return None

        # Update fields
        if user_data.email is not None:
            user.email = user_data.email
        if user_data.password is not None:
            user.password_hash = get_password_hash(user_data.password)
        if user_data.is_active is not None:
            user.is_active = user_data.is_active

        await db.flush()
        await db.refresh(user)

        return user

    @staticmethod
    async def delete_user(db: AsyncSession, user_id: int) -> bool:
        """
        Delete user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            bool: True if deleted, False if not found
        """
        user = await UserService.get_user_by_id(db, user_id)

        if not user:
            return False

        await db.delete(user)
        return True
