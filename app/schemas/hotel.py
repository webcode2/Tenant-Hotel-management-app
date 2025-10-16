"""Hotel schemas."""
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class HotelBase(BaseModel):
    """Base hotel schema."""

    name: str
    address: Optional[str] = None


class HotelCreate(HotelBase):
    """Schema for creating a new hotel."""

    pass


class HotelUpdate(BaseModel):
    """Schema for updating a hotel."""

    name: Optional[str] = None
    address: Optional[str] = None


class HotelResponse(HotelBase):
    """Schema for hotel response."""

    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
