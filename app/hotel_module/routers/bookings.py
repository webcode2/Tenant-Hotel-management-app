"""Booking router."""
from fastapi import APIRouter,  Depends, HTTPException, status, Path
from sqlalchemy.ext.asyncio import AsyncSession

# Assuming these dependencies and models are in your project structure
from app.core.database import get_db
from app.core.dependencies import require_role
from app.account_module.models.user import User
from app.hotel_module.schemas.bookingSchema import BookingCreate, BookingUpdate, BookingDetailResponse, BookingListMetadata
from app.hotel_module.services.booking_service import BookingService

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post("/", response_model=BookingDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_data: BookingCreate,
    # Anyone can create bookings
    db: AsyncSession = Depends(get_db)
) -> BookingDetailResponse:
    """
    Create a new room booking (Guest only).

    Args:
        booking_data: Booking creation data
        current_user: Current authenticated user (Guest role)
        db: Database session

    Returns:
        BookingDetailResponse: Created booking
    """
    booking = await BookingService.create_booking(db=db, booking_data=booking_data, )
    return BookingDetailResponse.model_validate(booking)


@router.get("/me/{customer}", response_model=list[BookingListMetadata])
async def get_my_bookings(
    customer: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_role(["Guest", "Admin", "Manager"])),
    db: AsyncSession = Depends(get_db)
) -> list[BookingListMetadata]:
    """
    Get bookings made by the current user (Guest, Admin, or Manager).

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Current authenticated user
        db: Database session

    Returns:
        list[BookingListMetadata]: list of bookings
    """
    # Admins/Managers can see all, Guests only see their own
    if hasattr(current_user, 'roles') and ("Admin" in current_user.roles or "Manager" in current_user.roles):
        # If Admin/Manager, this route can be adapted to return all bookings, or they can use the / route
        # For simplicity, let's have them use the general GET /bookings below
        bookings = await BookingService.get_all_bookings(db=db, skip=skip, limit=limit)
    else:
        bookings = await BookingService.get_bookings_by_customer(db=db, customer_contact=customer, skip=skip, limit=limit)

    return [BookingListMetadata.model_validate(booking) for booking in bookings]


@router.get("/", response_model=list[BookingListMetadata])
async def get_all_bookings(
    skip: int = 0,
    limit: int = 100,
    # Only Admin/Manager can see all
    current_user: User = Depends(require_role(["Admin", "Manager"])),
    db: AsyncSession = Depends(get_db)
) -> list[BookingListMetadata]:
    """
    Get all bookings with pagination (Admin or Manager only).

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Current authenticated user with Admin/Manager role
        db: Database session

    Returns:
        list[BookingListMetadata]: list of bookings
    """
    bookings = await BookingService.get_all_bookings(db, skip, limit)
    return [BookingListMetadata.model_validate(booking) for booking in bookings]


@router.get("/{booking_id}", response_model=BookingDetailResponse)
async def get_booking(
    booking_id: int = Path(..., description="The ID of the booking"),
    current_user: User = Depends(require_role(["Admin", "Manager", "Guest"])),
    db: AsyncSession = Depends(get_db)
) -> BookingDetailResponse:
    """
    Get booking by ID (Admin, Manager, or the Guest who made the booking).

    Args:
        booking_id: Booking ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        BookingDetailResponse: Booking data

    Raises:
        HTTPException: If booking not found or unauthorized
    """
    booking = await BookingService.get_booking_by_id(db, booking_id)

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    # Authorization check: only Admin, Manager, or the owner can view
    if "Admin" not in current_user.roles and "Manager" not in current_user.roles and booking.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this booking"
        )

    return BookingDetailResponse.model_validate(booking)


@router.put("/{booking_id}", response_model=BookingDetailResponse)
async def update_booking(
    booking_data: BookingUpdate,
    booking_id: int = Path(..., description="The ID of the booking"),
    db: AsyncSession = Depends(get_db)
) -> BookingDetailResponse:
    """
    Update booking (Admin, Manager, or the Guest who made the booking).

    Args:
        booking_id: Booking ID
        booking_data: Update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        BookingDetailResponse: Updated booking

    Raises:
        HTTPException: If booking not found or unauthorized
    """
    booking = await BookingService.get_booking_by_id(db, booking_id)

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    updated_booking = await BookingService.update_booking(db, booking_id, booking_data)

    if not updated_booking:
        # This should only happen if another process deleted it between fetch and update
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found after attempting update"
        )

    return BookingDetailResponse.model_validate(updated_booking)


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_booking(
    booking_id: int = Path(..., description="The ID of the booking"),
    # This dependency will automatically return 401 if the user is not authenticated.
    current_user: User = Depends(require_role(["Admin", "Manager", "Guest"])),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Cancel/Delete booking. Only allowed for Admin, Manager, or the logged-in 
    Guest who made the booking.

    Args:
        booking_id: Booking ID
        current_user: Current authenticated user (guaranteed to be logged in)
        db: Database session

    Raises:
        HTTPException: 
            - 401 UNAUTHORIZED (handled by dependency)
            - 404 NOT FOUND
            - 403 FORBIDDEN (if user is not staff/owner)
    """
    booking = await BookingService.get_booking_by_id(db, booking_id)

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    # Authorization Check (Safely checking roles to prevent AttributeError)

    # Staff check: Check if current_user has roles AND if they contain Admin/Manager
    is_staff = (
        hasattr(current_user, 'roles') and
        ("Admin" in current_user.roles or "Manager" in current_user.roles)
    )

    # Owner check: Check if the current user's authenticated email matches the booking contact
    # NOTE: Assuming 'current_user' always has an 'email' attribute if authentication succeeded.
    is_owner = booking.customer_contact == current_user.email

    if not (is_staff or is_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this booking"
        )

    success = await BookingService.delete_booking(db, booking_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete booking"
        )
