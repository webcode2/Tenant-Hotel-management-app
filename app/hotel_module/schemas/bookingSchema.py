
# Pydantic Schemas for Booking
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class BookingBase(BaseModel):
    """Base booking schema."""
    customer_contact: str
    check_in_date: date
    check_out_date: date
    num_guests: int
    total_price: int
    status: str = "pending"  # Default status


class BookingCreate(BookingBase):
    """Schema for creating a new booking."""
    room_id: int  # Required foreign key


class BookingUpdate(BaseModel):
    """Schema for updating a booking. All fields are optional."""
    customer_contact: Optional[str] = None
    check_in_date: Optional[date] = None
    check_out_date: Optional[date] = None
    num_guests: Optional[int] = None
    total_price: Optional[int] = None
    status: Optional[str] = None  # For confirmation, cancellation, etc.


class BookingDetailResponse(BookingBase):
    """Schema for a single booking detail response."""
    id: int
    room_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BookingListMetadata(BaseModel):
    """Schema for booking metadata in a list response."""
    id: int
    room_id: int
    customer_contact: str
    check_in_date: date
    check_out_date: date
    total_price: int
    status: str

    model_config = ConfigDict(from_attributes=True)
