"""Authentication service."""
from datetime import timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.schemas.user import UserCreate, UserLogin
from app.schemas.token import Token
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.config import settings


class AuthService:
    """Service for authentication operations."""

    @staticmethod
    async def register_user(db: AsyncSession, user_data: UserCreate) -> User:
        """
        Register a new user.

        Args:
            db: Database session
            user_data: User registration data

        Returns:
            User: Created user

        Raises:
            ValueError: If email already exists
        """
        # Check if user already exists
        result = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise ValueError("Email already registered")

        # Create new user
        user = User(
            email=user_data.email,
            password_hash=get_password_hash(user_data.password),
            is_active=True
        )

        db.add(user)
        await db.flush()
        await db.refresh(user)

        return user

    @staticmethod
    async def authenticate_user(db: AsyncSession, credentials: UserLogin) -> Optional[User]:
        """
        Authenticate a user.

        Args:
            db: Database session
            credentials: Login credentials

        Returns:
            Optional[User]: Authenticated user or None if invalid
        """
        result = await db.execute(
            select(User).where(User.email == credentials.email)
        )
        user = result.scalar_one_or_none()

        if not user:
            return None

        if not verify_password(credentials.password, user.password_hash):
            return None

        if not user.is_active:
            return None

        return user

    @staticmethod
    def create_user_token(user: User) -> Token:
        """
        Create JWT token for user.

        Args:
            user: User to create token for

        Returns:
            Token: JWT access token
        """
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )

        return Token(access_token=access_token, token_type="bearer")
