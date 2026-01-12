"""Customer model for storage renters."""
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.domain.models.base import TenantScopedEntity


class CustomerType(str, Enum):
    """Type of customer."""

    INDIVIDUAL = "individual"
    BUSINESS = "business"


class Customer(TenantScopedEntity):
    """Customer/renter model."""

    # Identification
    customer_type: CustomerType = Field(default=CustomerType.INDIVIDUAL)
    cedula: Optional[str] = Field(None, max_length=20, description="National ID (cédula)")
    cedula_juridica: Optional[str] = Field(None, max_length=20, description="Business ID")

    # Personal/Business info
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    company_name: Optional[str] = Field(None, max_length=255)

    # Contact
    email: EmailStr
    phone: str = Field(..., max_length=20)
    phone_secondary: Optional[str] = Field(None, max_length=20)

    # Address
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    province: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: str = Field(default="CR", max_length=2)

    # Emergency contact
    emergency_contact_name: Optional[str] = Field(None, max_length=200)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)

    # Preferences
    preferred_language: str = Field(default="es")
    accepts_email_notifications: bool = Field(default=True)
    accepts_sms_notifications: bool = Field(default=False)

    # Status
    is_active: bool = Field(default=True)
    notes: Optional[str] = Field(None, max_length=2000)

    @property
    def display_name(self) -> str:
        """Get display name for customer."""
        if self.customer_type == CustomerType.BUSINESS and self.company_name:
            return self.company_name
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name


class CustomerCreate(BaseModel):
    """Schema for creating a customer."""

    customer_type: CustomerType = Field(default=CustomerType.INDIVIDUAL)
    cedula: Optional[str] = Field(None, max_length=20)
    cedula_juridica: Optional[str] = Field(None, max_length=20)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    company_name: Optional[str] = Field(None, max_length=255)
    email: EmailStr
    phone: str = Field(..., max_length=20)
    phone_secondary: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    province: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: str = Field(default="CR", max_length=2)
    emergency_contact_name: Optional[str] = Field(None, max_length=200)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    preferred_language: str = Field(default="es")
    accepts_email_notifications: bool = Field(default=True)
    accepts_sms_notifications: bool = Field(default=False)
    notes: Optional[str] = Field(None, max_length=2000)


class CustomerUpdate(BaseModel):
    """Schema for updating a customer."""

    customer_type: Optional[CustomerType] = None
    cedula: Optional[str] = Field(None, max_length=20)
    cedula_juridica: Optional[str] = Field(None, max_length=20)
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    company_name: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    phone_secondary: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    province: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=2)
    emergency_contact_name: Optional[str] = Field(None, max_length=200)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    preferred_language: Optional[str] = None
    accepts_email_notifications: Optional[bool] = None
    accepts_sms_notifications: Optional[bool] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=2000)
