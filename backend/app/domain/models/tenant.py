"""Tenant model for multi-tenancy support."""
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.domain.models.base import BaseEntity


class TenantBase(BaseModel):
    """Base tenant fields."""

    name: str = Field(..., min_length=1, max_length=255, description="Business name")
    legal_name: Optional[str] = Field(None, max_length=255, description="Legal/registered name")
    cedula_juridica: Optional[str] = Field(None, max_length=20, description="Costa Rica business ID")
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    province: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: str = Field(default="CR", max_length=2)
    currency: str = Field(default="CRC", max_length=3)
    timezone: str = Field(default="America/Costa_Rica")
    locale: str = Field(default="es")
    sinpe_number: Optional[str] = Field(None, max_length=20, description="SINPE Móvil number for payments")
    is_active: bool = Field(default=True)


class TenantCreate(TenantBase):
    """Schema for creating a new tenant."""

    pass


class TenantUpdate(BaseModel):
    """Schema for updating a tenant."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    legal_name: Optional[str] = Field(None, max_length=255)
    cedula_juridica: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    province: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    sinpe_number: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None


class Tenant(TenantBase, BaseEntity):
    """Full tenant model with ID and timestamps."""

    pass
