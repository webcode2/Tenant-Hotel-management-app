"""Booking model representing a reservation for a specific room."""
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from app.core.database import Base
# NOTE: Replace '.base import Base' with your actual import path for your declarative base class.


class Booking(Base):
    """Booking model representing a reservation for a specific room."""

    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign Key linking to the Room model
    room_id = Column(Integer, ForeignKey("rooms.id"),
                     nullable=False, index=True)
    customer_contact = Column(String(255), nullable=False)

    # Dates and Capacity
    check_in_date = Column(Date, nullable=False)
    check_out_date = Column(Date, nullable=False)
    num_guests = Column(Integer, nullable=False)

    # Financial and Status
    # Storing price as an Integer (e.g., in cents or smallest currency unit)
    total_price = Column(Integer, nullable=False)
    # e.g., 'pending', 'confirmed', 'cancelled'
    status = Column(String(50), default="pending", nullable=False)

    # Audit Field
    created_at = Column(DateTime(timezone=True),
                        server_default=func.now(), nullable=False)

    # Relationships (Assuming a 'Room' model exists with 'bookings' back_populates)
    room = relationship("Room", )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<Booking(id={self.id}, room={self.room_id}, "
            f"in={self.check_in_date}, status={self.status})>"
        )
