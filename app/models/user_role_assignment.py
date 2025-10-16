"""User role assignment model."""
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserRoleAssignment(Base):
    """
    User role assignment model.

    Links users to roles with optional hotel scoping.
    - If hotel_id is NULL, the role applies globally (system-wide)
    - If hotel_id is set, the role is scoped to that specific hotel
    """

    __tablename__ = "user_role_assignments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    hotel_id = Column(Integer, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=True)

    # Relationships
    user = relationship("User", back_populates="role_assignments")
    role = relationship("Role", back_populates="user_assignments")
    hotel = relationship("Hotel", back_populates="user_role_assignments")

    def __repr__(self) -> str:
        """String representation."""
        scope = f"hotel_id={self.hotel_id}" if self.hotel_id else "global"
        return f"<UserRoleAssignment(user_id={self.user_id}, role_id={self.role_id}, {scope})>"
