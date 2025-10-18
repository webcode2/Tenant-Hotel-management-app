from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


# --- Helper Schemas for Structured Data ---

class Image(BaseModel):
    """Schema for a single hotel image reference."""
    public_id: str
    secure_url: str


class Area(BaseModel):
    """Structured address data for a hotel."""
    country: str
    state_or_province: str
    city_or_town: str
    county: str
    street: str
    zip_or_postal_code: str
    building_name_or_suite: Optional[str] = None


# --- Hotel Core Schemas ---

class HotelBase(BaseModel):
    """Base hotel schema, including all common fields."""

    # Core identification and description
    name: str
    description: Optional[str] = None

    # Structured address field (replaces the simple 'address' string)
    area: Area  # Required upon creation/base definition

    # Media fields
    cover_image_url: Optional[str] = None
    other_images: List[Image] = []  # Defaults to empty List

    # Feature field
    facilities: List[str] = []  # Defaults to empty List


class HotelCreate(HotelBase):
    """Schema for creating a new hotel. Inherits all required fields from HotelBase."""

    # Note: No additional fields needed, but validation will enforce
    # that 'name' and 'area' are present.
    pass


class HotelUpdate(BaseModel):
    """Schema for updating a hotel. All fields are optional."""

    name: Optional[str] = None
    description: Optional[str] = None

    # When updating, the entire area object must be provided if changing the address
    area: Optional[Area] = None

    cover_image_url: Optional[str] = None
    # For updating lists, the client usually sends the full, new List (e.g., facilities)
    other_images: Optional[List[Image]] = None
    facilities: Optional[List[str]] = None


class HotelResponse(HotelBase):
    """Schema for hotel response, including database-managed fields."""

    id: int
    created_at: datetime

    # The model_config tells Pydantic to read data from ORM objects (SQLAlchemy models)
    model_config = ConfigDict(from_attributes=True)


class HotelSingleResponse(HotelBase):
    """
    Schema for a full hotel detail response. 
    Used for single GET requests and as the response after creation (POST).
    """

    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HotelListMetadata(BaseModel):
    """
    Schema for a hotel entry in a List response (metadata only). 
    Excludes large fields like description, other_images, and facilities.
    """
    id: int
    name: str
    area: Area
    cover_image_url: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HotelListResponse(BaseModel):
    """Wrapper schema for returning a List of hotel metadata."""

    # You might include pagination metadata here later, but for now, just the List
    items: List[HotelListMetadata]

    model_config = ConfigDict(from_attributes=True)
