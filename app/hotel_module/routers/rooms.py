"""Room router."""
from fastapi import APIRouter, Body, Depends, HTTPException, status, Path
from sqlalchemy.ext.asyncio import AsyncSession

# Assuming these dependencies and models are in your project structure
from app.core.database import get_db
from app.core.dependencies import require_role
from app.account_module.models.user import User
from app.hotel_module.schemas.room import RoomCreate, RoomUpdate, RoomDetailResponse, RoomListMetadata
from app.hotel_module.services.room_service import RoomService

# Note: The prefix assumes the router will be included at the /hotels/{hotel_id} level
# This results in paths like: /hotels/{hotel_id}/rooms
router = APIRouter(prefix="/rooms", tags=["Rooms"])


@router.post(
    "/",
    response_model=RoomDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_room(
    room_data: RoomCreate,
    current_user: User = Depends(require_role(["Admin", "Manager"])),
    db: AsyncSession = Depends(get_db)
) -> RoomDetailResponse:
    """
    Create a new room for a specific hotel (Admin or Manager).

    Args:
        hotel_id: The ID of the hotel to add the room to (from path)
        room_data: Room creation data
        current_user: Current authenticated user
        db: Database session

    Returns:
        RoomDetailResponse: Created room
    """
    room = await RoomService.create_room(db=db, room_data=room_data)
    # The hotel_id is now explicitly handled in the service layer
    return RoomDetailResponse.model_validate(room)


@router.get("/",    response_model=list[RoomListMetadata])
async def get_all_rooms_in_hotel(
    hotel_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_role(["Admin", "Manager", "Guest"])),
    db: AsyncSession = Depends(get_db)
) -> list[RoomListMetadata]:
    """
    Get all rooms in a specific hotel with pagination (All authenticated users).

    Args:
        hotel_id: The ID of the hotel (from path)
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Current authenticated user
        db: Database session

    Returns:
        list[RoomListMetadata]: list of rooms
    """
    rooms = await RoomService.get_all_rooms_by_hotel(db, hotel_id, skip, limit)
    return [RoomListMetadata.model_validate(room) for room in rooms]


@router.get("/{room_id}",    response_model=RoomDetailResponse)
async def get_room(room_id: int = Path(..., description="The ID of the room"),
                   hotel_id: int = 0,
                   current_user: User = Depends(require_role(
                       ["Admin", "Manager", "Receiptionist", "Guest"])),
                   db: AsyncSession = Depends(get_db)
                   ) -> RoomDetailResponse:
    """
    Get room by ID within a hotel (All authenticated users).

    Args:
        room_id: Room ID
        hotel_id: Hotel ID (for context/validation)
        current_user: Current authenticated user
        db: Database session

    Returns:
        RoomDetailResponse: Room data

    Raises:
        HTTPException: If room not found
    """
    room = await RoomService.get_room_by_id(db=db, room_id=room_id)

    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found in this hotel"
        )

    return RoomDetailResponse.model_validate(room)


@router.get("/{room_name}",    response_model=RoomDetailResponse)
async def get_room_by_name(room_name: str = Path(..., description="The ID of the room"),
                           current_user: User = Depends(require_role(
                               ["Admin", "Manager", "Receiptionist", "Guest"])),
                           db: AsyncSession = Depends(get_db)
                           ) -> RoomDetailResponse:
    """
    Get room by name within a hotel (All authenticated users).

    Args:
        room_id: Room Name
        current_user: Current authenticated user
        db: Database session

    Returns:
        RoomDetailResponse: Room data

    Raises:
        HTTPException: If room not found
    """
    room = await RoomService.get_room_by_name(db=db, room_name=room_name)

    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found in this hotel"
        )

    return RoomDetailResponse.model_validate(room)


@router.put("/{room_id}",    response_model=RoomDetailResponse)
async def update_room(
    room_id: int = Path(..., description="The ID of the room"),
    hotel_id: int = 0,
    room_data: RoomUpdate = Body(default=None),
    current_user: User = Depends(require_role(["Admin", "Manager"])),
    db: AsyncSession = Depends(get_db)
) -> RoomDetailResponse:
    """
    Update room (Admin or Manager only).

    Args:
        room_id: Room ID
        hotel_id: Hotel ID
        room_data: Update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        RoomDetailResponse: Updated room

    Raises:
        HTTPException: If room not found
    """
    room = await RoomService.update_room(db=db, room_id=room_id, room_data=room_data)

    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found in this hotel"
        )

    return RoomDetailResponse.model_validate(room)


@router.delete("/{room_id}",    status_code=status.HTTP_204_NO_CONTENT)
async def delete_room(
    room_id: int = Path(..., description="The ID of the room"),
    current_user: User = Depends(require_role(["Admin", "Manager"])),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete room (Admin or Manager only).

    Args:
        room_id: Room ID
        hotel_id: Hotel ID
        current_user: Current authenticated user
        db: Database session

    Raises:
        HTTPException: If room not found
    """
    success = await RoomService.delete_room(db=db, room_id=room_id, )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found in this hotel"
        )
