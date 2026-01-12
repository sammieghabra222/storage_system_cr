"""User model for authentication and authorization."""
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.domain.models.base import TenantScopedEntity


class UserRole(str, Enum):
    """User roles for authorization."""

    OWNER = "owner"  # Full access, can manage other users
    MANAGER = "manager"  # Can manage units, customers, contracts
    STAFF = "staff"  # Can view and update, limited creation
    VIEWER = "viewer"  # Read-only access


class UserBase(BaseModel):
    """Base user fields."""

    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    role: UserRole = Field(default=UserRole.STAFF)
    is_active: bool = Field(default=True)
    locale: str = Field(default="es")


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(..., min_length=8)
    tenant_id: UUID


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    locale: Optional[str] = None


class User(UserBase, TenantScopedEntity):
    """Full user model with ID and timestamps."""

    hashed_password: str = Field(..., exclude=True)

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"


class UserPublic(UserBase):
    """Public user info (without sensitive data)."""

    id: UUID
    tenant_id: UUID

    class Config:
        from_attributes = True
