"""Hotel service."""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.hotel import Hotel
from app.schemas.hotel import HotelCreate, HotelUpdate


class HotelService:
    """Service for hotel operations."""

    @staticmethod
    async def create_hotel(db: AsyncSession, hotel_data: HotelCreate) -> Hotel:
        """
        Create a new hotel.

        Args:
            db: Database session
            hotel_data: Hotel creation data

        Returns:
            Hotel: Created hotel
        """
        hotel = Hotel(
            name=hotel_data.name,
            address=hotel_data.address
        )

        db.add(hotel)
        await db.flush()
        await db.refresh(hotel)

        return hotel

    @staticmethod
    async def get_hotel_by_id(db: AsyncSession, hotel_id: int) -> Optional[Hotel]:
        """
        Get hotel by ID.

        Args:
            db: Database session
            hotel_id: Hotel ID

        Returns:
            Optional[Hotel]: Hotel or None if not found
        """
        result = await db.execute(select(Hotel).where(Hotel.id == hotel_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all_hotels(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Hotel]:
        """
        Get all hotels with pagination.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List[Hotel]: List of hotels
        """
        result = await db.execute(select(Hotel).offset(skip).limit(limit))
        return list(result.scalars().all())

    @staticmethod
    async def update_hotel(
        db: AsyncSession,
        hotel_id: int,
        hotel_data: HotelUpdate
    ) -> Optional[Hotel]:
        """
        Update hotel.

        Args:
            db: Database session
            hotel_id: Hotel ID
            hotel_data: Update data

        Returns:
            Optional[Hotel]: Updated hotel or None if not found
        """
        hotel = await HotelService.get_hotel_by_id(db, hotel_id)

        if not hotel:
            return None

        if hotel_data.name is not None:
            hotel.name = hotel_data.name
        if hotel_data.address is not None:
            hotel.address = hotel_data.address

        await db.flush()
        await db.refresh(hotel)

        return hotel

    @staticmethod
    async def delete_hotel(db: AsyncSession, hotel_id: int) -> bool:
        """
        Delete hotel.

        Args:
            db: Database session
            hotel_id: Hotel ID

        Returns:
            bool: True if deleted, False if not found
        """
        hotel = await HotelService.get_hotel_by_id(db, hotel_id)

        if not hotel:
            return False

        await db.delete(hotel)
        return True
