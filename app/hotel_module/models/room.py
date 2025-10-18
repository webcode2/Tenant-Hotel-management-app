from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
# Assuming PostgreSQL for JSONB, adjust import if using a different dialect
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base


class Room(Base):
    """Room model representing a specific room within a Hotel."""

    __tablename__ = "rooms"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)

    # Foreign Key (Links to the Hotel model)
    # The type is Integer because the Hotel's primary key is Integer
    hotel_id = Column(Integer, ForeignKey("hotels.id"),
                      nullable=False, index=True)

    # Core Fields
    room_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    # e.g., 'available', 'booked', 'maintenance'
    status = Column(String(50), nullable=False, default="available")

    # Numeric/Capacity Fields
    # Store price as an integer (e.g., in cents/smallest currency unit)
    price_per_night = Column(Integer, nullable=False)
    max_occupancy = Column(Integer, nullable=False)
    number_of_beds = Column(Integer, nullable=False)

    # Structured Data Fields
    # Stores a JSON array of strings: ["air conditioning", "minibar", ...]
    facilities = Column(JSONB, nullable=True, default=[])

    # Stores a JSON array of Image objects (matching the Image interface)
    # [{"public_id": "string", "secure_url": "string"}, ...]
    photos = Column(JSONB, nullable=True, default=[])

    # Relationships
    # hotel = relationship("Hotel", back_populates="rooms")
    bookings = relationship("Booking", back_populates="room")

    # You might also add relationships for bookings, inventory, etc., here.

    def __repr__(self) -> str:
        """String representation."""
        return f"<Room(id={self.id}, type={self.room_type}, hotel_id={self.hotel_id})>"
