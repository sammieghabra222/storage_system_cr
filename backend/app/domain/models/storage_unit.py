"""Storage unit model."""
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.models.base import TenantScopedEntity


class UnitType(str, Enum):
    """Types of storage units."""

    STANDARD = "standard"
    CLIMATE_CONTROLLED = "climate_controlled"
    VEHICLE = "vehicle"
    LOCKER = "locker"
    OUTDOOR = "outdoor"


class UnitStatus(str, Enum):
    """Storage unit status."""

    AVAILABLE = "available"
    OCCUPIED = "occupied"
    RESERVED = "reserved"
    MAINTENANCE = "maintenance"
    UNAVAILABLE = "unavailable"


class StorageUnitBase(BaseModel):
    """Base storage unit fields."""

    unit_number: str = Field(..., min_length=1, max_length=50, description="Unit identifier (e.g., A-101)")
    unit_type: UnitType = Field(default=UnitType.STANDARD)
    status: UnitStatus = Field(default=UnitStatus.AVAILABLE)

    # Dimensions (in meters)
    width: Optional[Decimal] = Field(None, ge=0, description="Width in meters")
    length: Optional[Decimal] = Field(None, ge=0, description="Length in meters")
    height: Optional[Decimal] = Field(None, ge=0, description="Height in meters")

    # Pricing (in tenant's currency, default CRC)
    monthly_rate: Decimal = Field(..., ge=0, description="Monthly rental rate")
    deposit_amount: Optional[Decimal] = Field(None, ge=0, description="Security deposit")

    # Location within facility
    floor: Optional[int] = Field(None, ge=0, description="Floor number (0 = ground)")
    building: Optional[str] = Field(None, max_length=50, description="Building identifier")
    zone: Optional[str] = Field(None, max_length=50, description="Zone within facility")

    # Features
    has_electricity: bool = Field(default=False)
    has_climate_control: bool = Field(default=False)
    is_drive_up: bool = Field(default=False)
    is_indoor: bool = Field(default=True)

    notes: Optional[str] = Field(None, max_length=1000)


class StorageUnitCreate(StorageUnitBase):
    """Schema for creating a storage unit."""

    pass


class StorageUnitUpdate(BaseModel):
    """Schema for updating a storage unit."""

    unit_number: Optional[str] = Field(None, min_length=1, max_length=50)
    unit_type: Optional[UnitType] = None
    status: Optional[UnitStatus] = None
    width: Optional[Decimal] = Field(None, ge=0)
    length: Optional[Decimal] = Field(None, ge=0)
    height: Optional[Decimal] = Field(None, ge=0)
    monthly_rate: Optional[Decimal] = Field(None, ge=0)
    deposit_amount: Optional[Decimal] = Field(None, ge=0)
    floor: Optional[int] = Field(None, ge=0)
    building: Optional[str] = Field(None, max_length=50)
    zone: Optional[str] = Field(None, max_length=50)
    has_electricity: Optional[bool] = None
    has_climate_control: Optional[bool] = None
    is_drive_up: Optional[bool] = None
    is_indoor: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=1000)


class StorageUnit(StorageUnitBase, TenantScopedEntity):
    """Full storage unit model with ID and timestamps."""

    current_customer_id: Optional[UUID] = Field(None, description="Current renter if occupied")
    current_contract_id: Optional[UUID] = Field(None, description="Active contract if occupied")

    @property
    def area_sqm(self) -> Optional[Decimal]:
        """Calculate area in square meters."""
        if self.width and self.length:
            return self.width * self.length
        return None

    @property
    def volume_cbm(self) -> Optional[Decimal]:
        """Calculate volume in cubic meters."""
        if self.width and self.length and self.height:
            return self.width * self.length * self.height
        return None
