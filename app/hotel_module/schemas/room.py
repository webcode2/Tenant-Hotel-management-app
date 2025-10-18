"""Room schemas for API request and response validation."""
from typing import Optional
from pydantic import BaseModel, ConfigDict


# --- Helper Schema (reused from Hotel schemas) ---

class Image(BaseModel):
    """Schema for a single room image reference."""
    public_id: str
    secure_url: str


# --- Room Core Schemas ---

class RoomBase(BaseModel):
    """Base room schema, including all common fields."""
    name: str
    room_type: str
    # Assuming price is stored as integer (e.g., in cents)
    price_per_night: int
    max_occupancy: int
    status: str  # e.g., 'available', 'booked', 'maintenance'
    description: Optional[str] = None
    number_of_beds: int

    # Structured Data Fields
    # list of services/features (e.g., ["free wifi", "minibar"])
    facilities: list[str] = []
    photos: list[Image] = []  # list of Image objects


class RoomCreate(RoomBase):
    """Schema for creating a new room. Requires the ID of the parent hotel."""

    hotel_id: int  # Foreign key is required upon creation


class RoomUpdate(BaseModel):
    """Schema for updating a room. All fields are optional."""

    room_type: Optional[str] = None
    price_per_night: Optional[int] = None
    max_occupancy: Optional[int] = None
    status: Optional[str] = None
    description: Optional[str] = None
    number_of_beds: Optional[int] = None

    # When updating lists, the client usually sends the full, new list
    facilities: Optional[list[str]] = None
    photos: Optional[list[Image]] = None


# --- Room Response Schemas ---

class RoomDetailResponse(RoomBase):
    """
    Schema for the complete room detail page response. 
    Includes all fields from RoomBase, plus ID and the hotel ID.
    Used for single GET requests and as the response after creation (POST).
    """

    id: int
    hotel_id: int

    # Configuration to allow Pydantic to read data from SQLAlchemy ORM models
    model_config = ConfigDict(from_attributes=True)


class RoomListMetadata(BaseModel):
    """
    Schema for a room entry in a list response (metadata only). 
    Excludes large fields like description and the full photos list.
    """
    id: int
    name: str
    hotel_id: int
    room_type: str
    price_per_night: int
    max_occupancy: int
    status: str
    number_of_beds: int

    # We might include a simple thumbnail here if we modify the model,
    # but for now, we include the core metadata fields.

    model_config = ConfigDict(from_attributes=True)


class RoomListResponse(BaseModel):
    """Wrapper schema for returning a list of room metadata."""

    items: list[RoomListMetadata]

    model_config = ConfigDict(from_attributes=True)
