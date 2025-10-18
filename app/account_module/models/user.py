"""User model."""
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    """User model representing system and hotel users."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    role_assignments = relationship(
        "UserRoleAssignment",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    profile = relationship(
        "StaffProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<User(id={self.id}, email={self.email})>"


class StaffProfile(Base):
    """Profile model containing additional user details."""

    __tablename__ = "staffs_profile"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey(
        "users.id", ondelete="CASCADE"), nullable=False, unique=True)
    profile_img_url = Column(String, nullable=True)
    two_step_verified = Column(Boolean, default=False, nullable=False)
    two_factor_token = Column(String, nullable=True)

    # Relationships
    user = relationship("User", back_populates="profile", uselist=False)

    def __repr__(self) -> str:
        return f"<Profile(user_id={self.user_id}, two_step_verified={self.two_step_verified})>"
