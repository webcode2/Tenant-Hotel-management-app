from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.hotel_module.models.booking import Booking
from app.hotel_module.schemas.bookingSchema import BookingCreate, BookingUpdate


class BookingService:
    """Service for booking operations."""

    @staticmethod
    async def create_booking(db: AsyncSession, booking_data: BookingCreate) -> Booking:
        """
        Create a new room booking.

        Args:
            db: Database session
            booking_data: Booking creation data

        Returns:
            Booking: Created booking
        """
        booking_dict = booking_data.model_dump()
        booking = Booking(**booking_dict)

        db.add(booking)
        await db.flush()
        await db.refresh(booking)

        return booking

    @staticmethod
    async def get_all_bookings(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Booking]:
        """
        Get all bookings with pagination (Admin/Manager use).

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List[Booking]: List of all bookings
        """
        # Select all bookings, ordered by creation date descending (optional, but useful)
        stmt = select(Booking).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_booking_by_id(db: AsyncSession, booking_id: int) -> Optional[Booking]:
        """
        Get booking by ID.

        Args:
            db: Database session
            booking_id: Booking ID

        Returns:
            Optional[Booking]: Booking or None if not found
        """
        result = await db.execute(select(Booking).where(Booking.id == booking_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_bookings_by_customer(
        db: AsyncSession,
        customer_contact: int,
        skip: int = 0,
        limit: int = 30
    ) -> List[Booking]:
        """
        Get all bookings made by a specific user with pagination.

        Args:
            db: Database session
            customer_contact: ID of the user who made the booking
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List[Booking]: List of bookings
        """
        result = await db.execute(
            select(Booking)
            .where(Booking.customer_contact == customer_contact)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def update_booking(
        db: AsyncSession,
        booking_id: int,
        booking_data: BookingUpdate
    ) -> Optional[Booking]:
        """
        Update booking details.

        Args:
            db: Database session
            booking_id: Booking ID
            booking_data: Update data

        Returns:
            Optional[Booking]: Updated booking or None if not found
        """
        booking = await BookingService.get_booking_by_id(db, booking_id)

        if not booking:
            return None

        update_data = booking_data.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(booking, key, value)

        await db.flush()
        await db.refresh(booking)

        return booking

    @staticmethod
    async def delete_booking(db: AsyncSession, booking_id: int) -> bool:
        """
        Delete booking.

        Args:
            db: Database session
            booking_id: Booking ID

        Returns:
            bool: True if deleted, False if not found
        """
        booking = await BookingService.get_booking_by_id(db, booking_id)

        if not booking:
            return False

        await db.delete(booking)
        return True
