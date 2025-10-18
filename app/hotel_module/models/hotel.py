from sqlalchemy import Column, Integer, String, Text, DateTime, func
from sqlalchemy.orm import relationship
# Assuming PostgreSQL for JSONB, adjust import if using a different dialect
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base

class Hotel(Base):
    """Hotel model representing a tenant in the multi-tenant system."""

    __tablename__ = "hotels"

    # Core Fields
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    # New field (or you can store the JSON {public_id, secure_url} as JSONB)
    cover_image_url = Column(String(255), nullable=True)
    area = Column(JSONB, nullable=False)  # New field
    other_images = Column(JSONB, nullable=True, default=[])  # New field
    facilities = Column(JSONB, nullable=True, default=[])  # New field
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True),
                        server_default=func.now(), nullable=False)

    # rooms = relationship("Room", back_populates="hotel",
    #                      cascade="all, delete-orphan")

    user_role_assignments = relationship(
        "UserRoleAssignment",
        back_populates="hotel",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Hotel(id={self.id}, name={self.name})>"
