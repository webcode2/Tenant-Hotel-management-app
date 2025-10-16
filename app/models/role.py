"""Role model."""
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Role(Base):
    """Role model for role-based access control."""

    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Relationships
    user_assignments = relationship(
        "UserRoleAssignment",
        back_populates="role",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Role(id={self.id}, name={self.name})>"
