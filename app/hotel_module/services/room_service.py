"""Room service."""
from typing import Optional, List
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.hotel_module.models.room import Room
from app.hotel_module.schemas.room import RoomCreate, RoomUpdate


class RoomService:
    """Service for room operations."""

    @staticmethod
    async def create_room(db: AsyncSession, room_data: RoomCreate) -> Room:
        """
        Create a new room associated with a hotel.

        Args:
            db: Database session
            room_data: Room creation data

        Returns:
            Room: Created room
        """
        # Convert Pydantic model to a dict, including defaults, ready for SQLAlchemy
        room_dict = room_data.model_dump()

        # Instantiate the SQLAlchemy model
        # Note: Depending on your SQLAlchemy setup, this may need manual field mapping
        room = Room(**room_dict)

        db.add(room)
        await db.flush()
        await db.refresh(room)

        return room

    @staticmethod
    async def get_room_by_name(db: AsyncSession, room_name: str) -> Optional[Room]:
        """
        Get room by ID.

        Args:
            db: Database session
            room_id: Room ID

        Returns:
            Optional[Room]: Room or None if not found
        """
        result = await db.execute(select(Room).where(Room.id == room_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_room_by_id(db: AsyncSession, room_id: int) -> Optional[Room]:
        """
        Get room by ID.

        Args:
            db: Database session
            room_id: Room ID

        Returns:
            Optional[Room]: Room or None if not found
        """
        result = await db.execute(select(Room).where(Room.id == room_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all_rooms_by_hotel(
        db: AsyncSession,
        hotel_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> list[Room]:
        """
        Get all rooms for a specific hotel with pagination.

        Args:
            db: Database session
            hotel_id: ID of the parent hotel
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List[Room]: List of rooms
        """
        # Query filters rooms by the parent hotel_id
        result = await db.execute(
            select(Room)
            .where(Room.hotel_id == hotel_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def update_room(
        db: AsyncSession,
        room_id: int,
        room_data: RoomUpdate
    ) -> Optional[Room]:
        """
        Update room.

        Args:
            db: Database session
            room_id: Room ID
            room_data: Update data

        Returns:
            Optional[Room]: Updated room or None if not found
        """
        room = await RoomService.get_room_by_id(db, room_id)

        if not room:
            return None

        # Use Pydantic's model_dump to get only the fields that were actually provided (set=True)
        update_data = room_data.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(room, key, value)

        await db.flush()
        await db.refresh(room)

        return room

    @staticmethod
    async def delete_room(db: AsyncSession, room_id: int) -> bool:
        """
        Delete room.

        Args:
            db: Database session
            room_id: Room ID

        Returns:
            bool: True if deleted, False if not found
        """
        room = await RoomService.get_room_by_id(db, room_id)

        if not room:
            return False

        await db.delete(room)
        return True
