"""Role schemas."""
from pydantic import BaseModel, ConfigDict
from typing import Optional


class RoleBase(BaseModel):
    """Base role schema."""

    name: str
    description: Optional[str] = None


class RoleCreate(RoleBase):
    """Schema for creating a new role."""

    pass


class RoleUpdate(BaseModel):
    """Schema for updating a role."""

    name: Optional[str] = None
    description: Optional[str] = None


class RoleResponse(RoleBase):
    """Schema for role response."""

    id: int

    model_config = ConfigDict(from_attributes=True)
