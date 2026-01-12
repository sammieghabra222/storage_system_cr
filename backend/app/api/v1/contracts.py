"""Contract management endpoints."""
from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.dependencies import Repos, CurrentUser, ManagerUser, CurrentTenantId
from app.domain.models import (
    Contract,
    ContractCreate,
    ContractUpdate,
    ContractStatus,
    UnitStatus,
    StorageUnitUpdate,
)

router = APIRouter()


class ContractResponse(BaseModel):
    """Contract response schema."""

    id: str
    contract_number: str
    customer_id: str
    unit_id: str
    status: str
    start_date: date
    end_date: date | None
    signed_date: date | None
    move_in_date: date | None
    move_out_date: date | None
    monthly_rate: Decimal
    effective_monthly_rate: Decimal
    deposit_amount: Decimal
    deposit_paid: bool
    deposit_returned: bool
    billing_cycle: str
    billing_day: int
    grace_period_days: int
    late_fee_amount: Decimal
    late_fee_percent: Decimal | None
    auto_renew: bool
    renewal_notice_days: int
    discount_percent: Decimal | None
    discount_reason: str | None
    requires_insurance: bool
    insurance_provider: str | None
    access_code: str | None
    access_hours: str | None
    is_month_to_month: bool
    special_terms: str | None
    internal_notes: str | None

    class Config:
        from_attributes = True


class ContractListResponse(BaseModel):
    """Paginated list of contracts."""

    items: List[ContractResponse]
    total: int
    skip: int
    limit: int


class MoveInRequest(BaseModel):
    """Request to process move-in."""

    move_in_date: date = date.today()
    deposit_paid: bool = False
    signed_date: date | None = None
    access_code: str | None = None


class MoveOutRequest(BaseModel):
    """Request to process move-out."""

    move_out_date: date = date.today()
    return_deposit: bool = False
    notes: str | None = None


def _contract_to_response(contract: Contract) -> ContractResponse:
    """Convert contract model to response."""
    return ContractResponse(
        id=str(contract.id),
        contract_number=contract.contract_number,
        customer_id=str(contract.customer_id),
        unit_id=str(contract.unit_id),
        status=contract.status.value,
        start_date=contract.start_date,
        end_date=contract.end_date,
        signed_date=contract.signed_date,
        move_in_date=contract.move_in_date,
        move_out_date=contract.move_out_date,
        monthly_rate=contract.monthly_rate,
        effective_monthly_rate=contract.effective_monthly_rate,
        deposit_amount=contract.deposit_amount,
        deposit_paid=contract.deposit_paid,
        deposit_returned=contract.deposit_returned,
        billing_cycle=contract.billing_cycle.value,
        billing_day=contract.billing_day,
        grace_period_days=contract.grace_period_days,
        late_fee_amount=contract.late_fee_amount,
        late_fee_percent=contract.late_fee_percent,
        auto_renew=contract.auto_renew,
        renewal_notice_days=contract.renewal_notice_days,
        discount_percent=contract.discount_percent,
        discount_reason=contract.discount_reason,
        requires_insurance=contract.requires_insurance,
        insurance_provider=contract.insurance_provider,
        access_code=contract.access_code,
        access_hours=contract.access_hours,
        is_month_to_month=contract.is_month_to_month,
        special_terms=contract.special_terms,
        internal_notes=contract.internal_notes,
    )


@router.get("", response_model=ContractListResponse)
async def list_contracts(
    tenant_id: CurrentTenantId,
    user: CurrentUser,
    repos: Repos,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None),
    customer_id: Optional[UUID] = Query(None),
    unit_id: Optional[UUID] = Query(None),
):
    """List contracts with optional filters."""
    if customer_id:
        contracts = await repos.contracts.get_by_customer(customer_id, tenant_id)
    elif unit_id:
        contracts = await repos.contracts.get_by_unit(unit_id, tenant_id)
    elif status:
        contracts = await repos.contracts.get_by_status(tenant_id, status)
    else:
        contracts = await repos.contracts.get_all_for_tenant(tenant_id, skip=skip, limit=limit)

    total = await repos.contracts.count_for_tenant(tenant_id)

    return ContractListResponse(
        items=[_contract_to_response(c) for c in contracts],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{contract_id}", response_model=ContractResponse)
async def get_contract(
    contract_id: UUID,
    tenant_id: CurrentTenantId,
    user: CurrentUser,
    repos: Repos,
):
    """Get a specific contract."""
    contract = await repos.contracts.get_by_id_for_tenant(contract_id, tenant_id)

    if contract is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found",
        )

    return _contract_to_response(contract)


@router.post("", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
async def create_contract(
    contract_data: ContractCreate,
    tenant_id: CurrentTenantId,
    user: ManagerUser,
    repos: Repos,
):
    """Create a new contract (draft)."""
    # Verify customer exists
    customer = await repos.customers.get_by_id_for_tenant(contract_data.customer_id, tenant_id)
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    # Verify unit exists and is available
    unit = await repos.storage_units.get_by_id_for_tenant(contract_data.unit_id, tenant_id)
    if unit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Storage unit not found",
        )

    if unit.status != UnitStatus.AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Unit is not available (current status: {unit.status.value})",
        )

    # Check for active contracts on this unit
    active = await repos.contracts.get_active_for_unit(contract_data.unit_id, tenant_id)
    if active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unit already has an active contract",
        )

    contract = await repos.contracts.create_for_tenant(tenant_id, contract_data)

    # Mark unit as reserved
    await repos.storage_units.update(
        unit.id,
        StorageUnitUpdate(status=UnitStatus.RESERVED),
    )

    return _contract_to_response(contract)


@router.patch("/{contract_id}", response_model=ContractResponse)
async def update_contract(
    contract_id: UUID,
    contract_data: ContractUpdate,
    tenant_id: CurrentTenantId,
    user: ManagerUser,
    repos: Repos,
):
    """Update a contract."""
    existing = await repos.contracts.get_by_id_for_tenant(contract_id, tenant_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found",
        )

    contract = await repos.contracts.update(contract_id, contract_data)
    return _contract_to_response(contract)


@router.post("/{contract_id}/move-in", response_model=ContractResponse)
async def process_move_in(
    contract_id: UUID,
    request: MoveInRequest,
    tenant_id: CurrentTenantId,
    user: ManagerUser,
    repos: Repos,
):
    """Process move-in for a contract."""
    contract = await repos.contracts.get_by_id_for_tenant(contract_id, tenant_id)
    if contract is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found",
        )

    if contract.status not in (ContractStatus.DRAFT, ContractStatus.ACTIVE):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot move in: contract status is {contract.status.value}",
        )

    # Update contract
    update = ContractUpdate(
        status=ContractStatus.ACTIVE,
        move_in_date=request.move_in_date,
        deposit_paid=request.deposit_paid,
        signed_date=request.signed_date or date.today(),
        terms_accepted=True,
    )
    if request.access_code:
        update.access_code = request.access_code

    contract = await repos.contracts.update(contract_id, update)

    # Update unit status and link to customer/contract
    await repos.storage_units.update(
        contract.unit_id,
        StorageUnitUpdate(
            status=UnitStatus.OCCUPIED,
        ),
    )

    # Update unit's current customer and contract (we need to handle this specially)
    unit = await repos.storage_units.get_by_id(contract.unit_id)
    unit.current_customer_id = contract.customer_id
    unit.current_contract_id = contract.id

    return _contract_to_response(contract)


@router.post("/{contract_id}/move-out", response_model=ContractResponse)
async def process_move_out(
    contract_id: UUID,
    request: MoveOutRequest,
    tenant_id: CurrentTenantId,
    user: ManagerUser,
    repos: Repos,
):
    """Process move-out for a contract."""
    contract = await repos.contracts.get_by_id_for_tenant(contract_id, tenant_id)
    if contract is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found",
        )

    if contract.status != ContractStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Contract is not active",
        )

    # Update contract
    update = ContractUpdate(
        status=ContractStatus.TERMINATED,
        move_out_date=request.move_out_date,
        deposit_returned=request.return_deposit,
        deposit_return_date=request.move_out_date if request.return_deposit else None,
    )
    if request.notes:
        update.internal_notes = (contract.internal_notes or "") + f"\nMove-out: {request.notes}"

    contract = await repos.contracts.update(contract_id, update)

    # Update unit status
    unit = await repos.storage_units.get_by_id(contract.unit_id)
    unit.current_customer_id = None
    unit.current_contract_id = None
    await repos.storage_units.update(
        contract.unit_id,
        StorageUnitUpdate(status=UnitStatus.AVAILABLE),
    )

    return _contract_to_response(contract)


@router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contract(
    contract_id: UUID,
    tenant_id: CurrentTenantId,
    user: ManagerUser,
    repos: Repos,
):
    """Delete a draft contract."""
    contract = await repos.contracts.get_by_id_for_tenant(contract_id, tenant_id)
    if contract is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found",
        )

    if contract.status != ContractStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Can only delete draft contracts",
        )

    # Release the unit reservation
    await repos.storage_units.update(
        contract.unit_id,
        StorageUnitUpdate(status=UnitStatus.AVAILABLE),
    )

    await repos.contracts.delete(contract_id)
