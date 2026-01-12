"""Customer management endpoints."""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, EmailStr

from app.dependencies import Repos, CurrentUser, StaffUser, CurrentTenantId
from app.domain.models import Customer, CustomerCreate, CustomerUpdate

router = APIRouter()


class CustomerResponse(BaseModel):
    """Customer response schema."""

    id: str
    customer_type: str
    cedula: str | None
    cedula_juridica: str | None
    first_name: str
    last_name: str | None
    company_name: str | None
    display_name: str
    email: str
    phone: str
    phone_secondary: str | None
    address: str | None
    city: str | None
    province: str | None
    postal_code: str | None
    country: str
    emergency_contact_name: str | None
    emergency_contact_phone: str | None
    preferred_language: str
    accepts_email_notifications: bool
    accepts_sms_notifications: bool
    is_active: bool
    notes: str | None

    class Config:
        from_attributes = True


class CustomerListResponse(BaseModel):
    """Paginated list of customers."""

    items: List[CustomerResponse]
    total: int
    skip: int
    limit: int


def _customer_to_response(customer: Customer) -> CustomerResponse:
    """Convert customer model to response."""
    return CustomerResponse(
        id=str(customer.id),
        customer_type=customer.customer_type.value,
        cedula=customer.cedula,
        cedula_juridica=customer.cedula_juridica,
        first_name=customer.first_name,
        last_name=customer.last_name,
        company_name=customer.company_name,
        display_name=customer.display_name,
        email=customer.email,
        phone=customer.phone,
        phone_secondary=customer.phone_secondary,
        address=customer.address,
        city=customer.city,
        province=customer.province,
        postal_code=customer.postal_code,
        country=customer.country,
        emergency_contact_name=customer.emergency_contact_name,
        emergency_contact_phone=customer.emergency_contact_phone,
        preferred_language=customer.preferred_language,
        accepts_email_notifications=customer.accepts_email_notifications,
        accepts_sms_notifications=customer.accepts_sms_notifications,
        is_active=customer.is_active,
        notes=customer.notes,
    )


@router.get("", response_model=CustomerListResponse)
async def list_customers(
    tenant_id: CurrentTenantId,
    user: CurrentUser,
    repos: Repos,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=1),
):
    """List all customers for the tenant."""
    if search:
        customers = await repos.customers.search(tenant_id, search, skip=skip, limit=limit)
        # For search, we don't have exact total count
        total = len(customers)
    else:
        customers = await repos.customers.get_all_for_tenant(tenant_id, skip=skip, limit=limit)
        total = await repos.customers.count_for_tenant(tenant_id)

    return CustomerListResponse(
        items=[_customer_to_response(c) for c in customers],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: UUID,
    tenant_id: CurrentTenantId,
    user: CurrentUser,
    repos: Repos,
):
    """Get a specific customer."""
    customer = await repos.customers.get_by_id_for_tenant(customer_id, tenant_id)

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    return _customer_to_response(customer)


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: CustomerCreate,
    tenant_id: CurrentTenantId,
    user: StaffUser,  # Staff+ can create
    repos: Repos,
):
    """Create a new customer."""
    # Check if email already exists for this tenant
    existing = await repos.customers.get_by_email(customer_data.email, tenant_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Customer with this email already exists",
        )

    # Check if cedula already exists (if provided)
    if customer_data.cedula:
        existing = await repos.customers.get_by_cedula(customer_data.cedula, tenant_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Customer with this cédula already exists",
            )

    customer = await repos.customers.create_for_tenant(tenant_id, customer_data)
    return _customer_to_response(customer)


@router.patch("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: UUID,
    customer_data: CustomerUpdate,
    tenant_id: CurrentTenantId,
    user: StaffUser,
    repos: Repos,
):
    """Update a customer."""
    existing = await repos.customers.get_by_id_for_tenant(customer_id, tenant_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    # Check email conflict
    if customer_data.email and customer_data.email != existing.email:
        conflict = await repos.customers.get_by_email(customer_data.email, tenant_id)
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Customer with this email already exists",
            )

    # Check cedula conflict
    if customer_data.cedula and customer_data.cedula != existing.cedula:
        conflict = await repos.customers.get_by_cedula(customer_data.cedula, tenant_id)
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Customer with this cédula already exists",
            )

    customer = await repos.customers.update(customer_id, customer_data)
    return _customer_to_response(customer)


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: UUID,
    tenant_id: CurrentTenantId,
    user: StaffUser,
    repos: Repos,
):
    """Delete a customer."""
    existing = await repos.customers.get_by_id_for_tenant(customer_id, tenant_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    # Check for active contracts
    contracts = await repos.contracts.get_by_customer(customer_id, tenant_id)
    active_contracts = [c for c in contracts if c.status.value == "active"]
    if active_contracts:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete customer with active contracts",
        )

    await repos.customers.delete(customer_id)
