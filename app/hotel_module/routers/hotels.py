"""Hotels router."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_role
from app.account_module.models.user import User
from app.hotel_module.schemas.hotel import HotelCreate, HotelResponse, HotelUpdate
from app.hotel_module.services.hotel_service import HotelService

router = APIRouter(prefix="/hotels", tags=["Hotels"])


@router.post("/", response_model=HotelResponse, status_code=status.HTTP_201_CREATED)
async def create_hotel(
    hotel_data: HotelCreate,
    current_user: User = Depends(require_role(["Admin"])),
    db: AsyncSession = Depends(get_db)
) -> HotelResponse:
    """
    Create a new hotel (Admin only).

    Args:
        hotel_data: Hotel creation data
        current_user: Current authenticated user with Admin role
        db: Database session

    Returns:
        HotelResponse: Created hotel
    """
    hotel = await HotelService.create_hotel(db, hotel_data)
    return HotelResponse.model_validate(hotel)


@router.get("/", response_model=List[HotelResponse])
async def get_all_hotels(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_role(["Admin", "Manager"])),
    db: AsyncSession = Depends(get_db)
) -> List[HotelResponse]:
    """
    Get all hotels (Admin or Manager).

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Current authenticated user
        db: Database session

    Returns:
        List[HotelResponse]: List of hotels
    """
    hotels = await HotelService.get_all_hotels(db, skip, limit)
    return [HotelResponse.model_validate(hotel) for hotel in hotels]


@router.get("/{hotel_id}", response_model=HotelResponse)
async def get_hotel(
    hotel_id: int,
    current_user: User = Depends(require_role(["Admin", "Manager"])),
    db: AsyncSession = Depends(get_db)
) -> HotelResponse:
    """
    Get hotel by ID (Admin or Manager).

    Args:
        hotel_id: Hotel ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        HotelResponse: Hotel data

    Raises:
        HTTPException: If hotel not found
    """
    hotel = await HotelService.get_hotel_by_id(db, hotel_id)

    if not hotel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hotel not found"
        )

    return HotelResponse.model_validate(hotel)


@router.put("/{hotel_id}", response_model=HotelResponse)
async def update_hotel(
    hotel_id: int,
    hotel_data: HotelUpdate,
    current_user: User = Depends(require_role(["Admin"])),
    db: AsyncSession = Depends(get_db)
) -> HotelResponse:
    """
    Update hotel (Admin only).

    Args:
        hotel_id: Hotel ID
        hotel_data: Update data
        current_user: Current authenticated user with Admin role
        db: Database session

    Returns:
        HotelResponse: Updated hotel

    Raises:
        HTTPException: If hotel not found
    """
    hotel = await HotelService.update_hotel(db, hotel_id, hotel_data)

    if not hotel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hotel not found"
        )

    return HotelResponse.model_validate(hotel)


@router.delete("/{hotel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hotel(
    hotel_id: int,
    current_user: User = Depends(require_role(["Admin"])),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete hotel (Admin only).

    Args:
        hotel_id: Hotel ID
        current_user: Current authenticated user with Admin role
        db: Database session

    Raises:
        HTTPException: If hotel not found
    """
    success = await HotelService.delete_hotel(db, hotel_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hotel not found"
        )
