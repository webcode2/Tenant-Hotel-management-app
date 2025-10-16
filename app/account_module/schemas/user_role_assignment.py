"""User role assignment schemas."""
from pydantic import BaseModel, ConfigDict
from typing import Optional


class UserRoleAssignmentBase(BaseModel):
    """Base user role assignment schema."""

    user_id: int
    role_id: int
    hotel_id: Optional[int] = None


class UserRoleAssignmentCreate(UserRoleAssignmentBase):
    """Schema for creating a new user role assignment."""

    pass


class UserRoleAssignmentResponse(UserRoleAssignmentBase):
    """Schema for user role assignment response."""

    id: int

    model_config = ConfigDict(from_attributes=True)
