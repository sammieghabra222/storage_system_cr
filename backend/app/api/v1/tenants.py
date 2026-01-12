"""Tenant management endpoints."""
from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.dependencies import Repos, CurrentUser, OwnerUser, CurrentTenantId
from app.domain.models import Tenant, TenantUpdate

router = APIRouter()


class TenantResponse(BaseModel):
    """Tenant response schema."""

    id: str
    name: str
    legal_name: str | None
    cedula_juridica: str | None
    email: str
    phone: str | None
    address: str | None
    city: str | None
    province: str | None
    postal_code: str | None
    country: str
    currency: str
    timezone: str
    locale: str
    sinpe_number: str | None
    is_active: bool

    class Config:
        from_attributes = True


@router.get("/current", response_model=TenantResponse)
async def get_current_tenant(
    tenant_id: CurrentTenantId,
    user: CurrentUser,
    repos: Repos,
):
    """Get current tenant information."""
    tenant = await repos.tenants.get_by_id(tenant_id)

    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    return TenantResponse(
        id=str(tenant.id),
        name=tenant.name,
        legal_name=tenant.legal_name,
        cedula_juridica=tenant.cedula_juridica,
        email=tenant.email,
        phone=tenant.phone,
        address=tenant.address,
        city=tenant.city,
        province=tenant.province,
        postal_code=tenant.postal_code,
        country=tenant.country,
        currency=tenant.currency,
        timezone=tenant.timezone,
        locale=tenant.locale,
        sinpe_number=tenant.sinpe_number,
        is_active=tenant.is_active,
    )


@router.patch("/current", response_model=TenantResponse)
async def update_current_tenant(
    update: TenantUpdate,
    tenant_id: CurrentTenantId,
    user: OwnerUser,  # Only owners can update tenant
    repos: Repos,
):
    """Update current tenant information."""
    tenant = await repos.tenants.update(tenant_id, update)

    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    return TenantResponse(
        id=str(tenant.id),
        name=tenant.name,
        legal_name=tenant.legal_name,
        cedula_juridica=tenant.cedula_juridica,
        email=tenant.email,
        phone=tenant.phone,
        address=tenant.address,
        city=tenant.city,
        province=tenant.province,
        postal_code=tenant.postal_code,
        country=tenant.country,
        currency=tenant.currency,
        timezone=tenant.timezone,
        locale=tenant.locale,
        sinpe_number=tenant.sinpe_number,
        is_active=tenant.is_active,
    )
