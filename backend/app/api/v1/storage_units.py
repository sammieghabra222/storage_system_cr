"""Storage unit management endpoints."""
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.dependencies import Repos, CurrentUser, ManagerUser, CurrentTenantId
from app.domain.models import (
    StorageUnit,
    StorageUnitCreate,
    StorageUnitUpdate,
    UnitType,
    UnitStatus,
)

router = APIRouter()


class StorageUnitResponse(BaseModel):
    """Storage unit response schema."""

    id: str
    unit_number: str
    unit_type: str
    status: str
    width: Decimal | None
    length: Decimal | None
    height: Decimal | None
    monthly_rate: Decimal
    deposit_amount: Decimal | None
    floor: int | None
    building: str | None
    zone: str | None
    has_electricity: bool
    has_climate_control: bool
    is_drive_up: bool
    is_indoor: bool
    notes: str | None
    current_customer_id: str | None
    current_contract_id: str | None
    area_sqm: Decimal | None
    volume_cbm: Decimal | None

    class Config:
        from_attributes = True


class StorageUnitListResponse(BaseModel):
    """Paginated list of storage units."""

    items: List[StorageUnitResponse]
    total: int
    skip: int
    limit: int


class StorageUnitStats(BaseModel):
    """Storage unit statistics."""

    total: int
    available: int
    occupied: int
    reserved: int
    maintenance: int
    occupancy_rate: float


def _unit_to_response(unit: StorageUnit) -> StorageUnitResponse:
    """Convert storage unit model to response."""
    return StorageUnitResponse(
        id=str(unit.id),
        unit_number=unit.unit_number,
        unit_type=unit.unit_type.value,
        status=unit.status.value,
        width=unit.width,
        length=unit.length,
        height=unit.height,
        monthly_rate=unit.monthly_rate,
        deposit_amount=unit.deposit_amount,
        floor=unit.floor,
        building=unit.building,
        zone=unit.zone,
        has_electricity=unit.has_electricity,
        has_climate_control=unit.has_climate_control,
        is_drive_up=unit.is_drive_up,
        is_indoor=unit.is_indoor,
        notes=unit.notes,
        current_customer_id=str(unit.current_customer_id) if unit.current_customer_id else None,
        current_contract_id=str(unit.current_contract_id) if unit.current_contract_id else None,
        area_sqm=unit.area_sqm,
        volume_cbm=unit.volume_cbm,
    )


@router.get("", response_model=StorageUnitListResponse)
async def list_storage_units(
    tenant_id: CurrentTenantId,
    user: CurrentUser,
    repos: Repos,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None),
    unit_type: Optional[str] = Query(None),
):
    """List all storage units for the tenant."""
    if status:
        units = await repos.storage_units.get_by_status(tenant_id, status)
    else:
        units = await repos.storage_units.get_all_for_tenant(tenant_id, skip=skip, limit=limit)

    # Filter by type if specified
    if unit_type:
        units = [u for u in units if u.unit_type.value == unit_type]

    total = await repos.storage_units.count_for_tenant(tenant_id)

    return StorageUnitListResponse(
        items=[_unit_to_response(u) for u in units],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/stats", response_model=StorageUnitStats)
async def get_storage_unit_stats(
    tenant_id: CurrentTenantId,
    user: CurrentUser,
    repos: Repos,
):
    """Get storage unit statistics."""
    all_units = await repos.storage_units.get_all_for_tenant(tenant_id, skip=0, limit=10000)

    total = len(all_units)
    available = len([u for u in all_units if u.status == UnitStatus.AVAILABLE])
    occupied = len([u for u in all_units if u.status == UnitStatus.OCCUPIED])
    reserved = len([u for u in all_units if u.status == UnitStatus.RESERVED])
    maintenance = len([u for u in all_units if u.status == UnitStatus.MAINTENANCE])

    occupancy_rate = (occupied / total * 100) if total > 0 else 0

    return StorageUnitStats(
        total=total,
        available=available,
        occupied=occupied,
        reserved=reserved,
        maintenance=maintenance,
        occupancy_rate=round(occupancy_rate, 2),
    )


@router.get("/available", response_model=List[StorageUnitResponse])
async def list_available_units(
    tenant_id: CurrentTenantId,
    user: CurrentUser,
    repos: Repos,
):
    """List all available storage units."""
    units = await repos.storage_units.get_available_units(tenant_id)
    return [_unit_to_response(u) for u in units]


@router.get("/{unit_id}", response_model=StorageUnitResponse)
async def get_storage_unit(
    unit_id: UUID,
    tenant_id: CurrentTenantId,
    user: CurrentUser,
    repos: Repos,
):
    """Get a specific storage unit."""
    unit = await repos.storage_units.get_by_id_for_tenant(unit_id, tenant_id)

    if unit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Storage unit not found",
        )

    return _unit_to_response(unit)


@router.post("", response_model=StorageUnitResponse, status_code=status.HTTP_201_CREATED)
async def create_storage_unit(
    unit_data: StorageUnitCreate,
    tenant_id: CurrentTenantId,
    user: ManagerUser,  # Only managers+ can create
    repos: Repos,
):
    """Create a new storage unit."""
    # Check if unit number already exists
    existing = await repos.storage_units.get_by_unit_number(unit_data.unit_number, tenant_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Unit number '{unit_data.unit_number}' already exists",
        )

    unit = await repos.storage_units.create_for_tenant(tenant_id, unit_data)
    return _unit_to_response(unit)


@router.patch("/{unit_id}", response_model=StorageUnitResponse)
async def update_storage_unit(
    unit_id: UUID,
    unit_data: StorageUnitUpdate,
    tenant_id: CurrentTenantId,
    user: ManagerUser,
    repos: Repos,
):
    """Update a storage unit."""
    # Verify unit exists and belongs to tenant
    existing = await repos.storage_units.get_by_id_for_tenant(unit_id, tenant_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Storage unit not found",
        )

    # Check if new unit number conflicts
    if unit_data.unit_number and unit_data.unit_number != existing.unit_number:
        conflict = await repos.storage_units.get_by_unit_number(unit_data.unit_number, tenant_id)
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Unit number '{unit_data.unit_number}' already exists",
            )

    unit = await repos.storage_units.update(unit_id, unit_data)
    return _unit_to_response(unit)


@router.delete("/{unit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_storage_unit(
    unit_id: UUID,
    tenant_id: CurrentTenantId,
    user: ManagerUser,
    repos: Repos,
):
    """Delete a storage unit."""
    # Verify unit exists and belongs to tenant
    existing = await repos.storage_units.get_by_id_for_tenant(unit_id, tenant_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Storage unit not found",
        )

    # Don't allow deletion of occupied units
    if existing.status == UnitStatus.OCCUPIED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete an occupied unit",
        )

    await repos.storage_units.delete(unit_id)
