"""Invoice management endpoints."""
from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.dependencies import Repos, CurrentUser, ManagerUser, CurrentTenantId
from app.domain.models import (
    Invoice,
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceStatus,
    InvoiceLineItem,
)

router = APIRouter()


class InvoiceLineItemResponse(BaseModel):
    """Invoice line item response."""

    description: str
    quantity: Decimal
    unit_price: Decimal
    tax_rate: Decimal
    discount_percent: Decimal
    subtotal: Decimal
    tax_amount: Decimal
    total: Decimal


class InvoiceResponse(BaseModel):
    """Invoice response schema."""

    id: str
    invoice_number: str
    customer_id: str
    contract_id: str | None
    status: str
    issue_date: date
    due_date: date
    period_start: date | None
    period_end: date | None
    line_items: List[InvoiceLineItemResponse]
    subtotal: Decimal
    tax_total: Decimal
    discount_total: Decimal
    total: Decimal
    amount_paid: Decimal
    balance_due: Decimal
    currency: str
    late_fee_applied: bool
    late_fee_amount: Decimal
    is_overdue: bool
    hacienda_key: str | None
    hacienda_status: str | None
    notes: str | None

    class Config:
        from_attributes = True


class InvoiceListResponse(BaseModel):
    """Paginated list of invoices."""

    items: List[InvoiceResponse]
    total: int
    skip: int
    limit: int


class InvoiceSummary(BaseModel):
    """Invoice summary statistics."""

    total_invoices: int
    total_amount: Decimal
    total_paid: Decimal
    total_outstanding: Decimal
    overdue_count: int
    overdue_amount: Decimal


def _line_item_to_response(item: InvoiceLineItem) -> InvoiceLineItemResponse:
    """Convert line item to response."""
    return InvoiceLineItemResponse(
        description=item.description,
        quantity=item.quantity,
        unit_price=item.unit_price,
        tax_rate=item.tax_rate,
        discount_percent=item.discount_percent,
        subtotal=item.subtotal,
        tax_amount=item.tax_amount,
        total=item.total,
    )


def _invoice_to_response(invoice: Invoice) -> InvoiceResponse:
    """Convert invoice model to response."""
    return InvoiceResponse(
        id=str(invoice.id),
        invoice_number=invoice.invoice_number,
        customer_id=str(invoice.customer_id),
        contract_id=str(invoice.contract_id) if invoice.contract_id else None,
        status=invoice.status.value,
        issue_date=invoice.issue_date,
        due_date=invoice.due_date,
        period_start=invoice.period_start,
        period_end=invoice.period_end,
        line_items=[_line_item_to_response(item) for item in invoice.line_items],
        subtotal=invoice.subtotal,
        tax_total=invoice.tax_total,
        discount_total=invoice.discount_total,
        total=invoice.total,
        amount_paid=invoice.amount_paid,
        balance_due=invoice.balance_due,
        currency=invoice.currency,
        late_fee_applied=invoice.late_fee_applied,
        late_fee_amount=invoice.late_fee_amount,
        is_overdue=invoice.is_overdue,
        hacienda_key=invoice.hacienda_key,
        hacienda_status=invoice.hacienda_status,
        notes=invoice.notes,
    )


@router.get("", response_model=InvoiceListResponse)
async def list_invoices(
    tenant_id: CurrentTenantId,
    user: CurrentUser,
    repos: Repos,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None),
    customer_id: Optional[UUID] = Query(None),
    contract_id: Optional[UUID] = Query(None),
    overdue_only: bool = Query(False),
):
    """List invoices with optional filters."""
    if overdue_only:
        invoices = await repos.invoices.get_overdue(tenant_id)
    elif customer_id:
        invoices = await repos.invoices.get_by_customer(customer_id, tenant_id)
    elif contract_id:
        invoices = await repos.invoices.get_by_contract(contract_id, tenant_id)
    elif status:
        invoices = await repos.invoices.get_by_status(tenant_id, status)
    else:
        invoices = await repos.invoices.get_all_for_tenant(tenant_id, skip=skip, limit=limit)

    total = await repos.invoices.count_for_tenant(tenant_id)

    return InvoiceListResponse(
        items=[_invoice_to_response(i) for i in invoices],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/summary", response_model=InvoiceSummary)
async def get_invoice_summary(
    tenant_id: CurrentTenantId,
    user: CurrentUser,
    repos: Repos,
):
    """Get invoice summary statistics."""
    all_invoices = await repos.invoices.get_all_for_tenant(tenant_id, skip=0, limit=10000)
    overdue = await repos.invoices.get_overdue(tenant_id)

    total_amount = sum(i.total for i in all_invoices)
    total_paid = sum(i.amount_paid for i in all_invoices)
    total_outstanding = sum(i.balance_due for i in all_invoices)
    overdue_amount = sum(i.balance_due for i in overdue)

    return InvoiceSummary(
        total_invoices=len(all_invoices),
        total_amount=total_amount,
        total_paid=total_paid,
        total_outstanding=total_outstanding,
        overdue_count=len(overdue),
        overdue_amount=overdue_amount,
    )


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: UUID,
    tenant_id: CurrentTenantId,
    user: CurrentUser,
    repos: Repos,
):
    """Get a specific invoice."""
    invoice = await repos.invoices.get_by_id_for_tenant(invoice_id, tenant_id)

    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    return _invoice_to_response(invoice)


@router.post("", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice_data: InvoiceCreate,
    tenant_id: CurrentTenantId,
    user: ManagerUser,
    repos: Repos,
):
    """Create a new invoice."""
    # Verify customer exists
    customer = await repos.customers.get_by_id_for_tenant(invoice_data.customer_id, tenant_id)
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    # Verify contract if provided
    if invoice_data.contract_id:
        contract = await repos.contracts.get_by_id_for_tenant(invoice_data.contract_id, tenant_id)
        if contract is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contract not found",
            )

    invoice = await repos.invoices.create_for_tenant(tenant_id, invoice_data)
    return _invoice_to_response(invoice)


@router.patch("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: UUID,
    invoice_data: InvoiceUpdate,
    tenant_id: CurrentTenantId,
    user: ManagerUser,
    repos: Repos,
):
    """Update an invoice."""
    existing = await repos.invoices.get_by_id_for_tenant(invoice_id, tenant_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    # Don't allow editing paid/cancelled invoices
    if existing.status in (InvoiceStatus.PAID, InvoiceStatus.CANCELLED, InvoiceStatus.REFUNDED):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot modify invoice with status: {existing.status.value}",
        )

    invoice = await repos.invoices.update(invoice_id, invoice_data)
    return _invoice_to_response(invoice)


@router.post("/{invoice_id}/send", response_model=InvoiceResponse)
async def send_invoice(
    invoice_id: UUID,
    tenant_id: CurrentTenantId,
    user: ManagerUser,
    repos: Repos,
):
    """Mark invoice as sent (email would be sent in production)."""
    invoice = await repos.invoices.get_by_id_for_tenant(invoice_id, tenant_id)
    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    if invoice.status != InvoiceStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Invoice has already been sent",
        )

    # TODO: Send email notification to customer

    invoice = await repos.invoices.update(
        invoice_id,
        InvoiceUpdate(status=InvoiceStatus.SENT),
    )
    return _invoice_to_response(invoice)


@router.post("/{invoice_id}/cancel", response_model=InvoiceResponse)
async def cancel_invoice(
    invoice_id: UUID,
    tenant_id: CurrentTenantId,
    user: ManagerUser,
    repos: Repos,
):
    """Cancel an invoice."""
    invoice = await repos.invoices.get_by_id_for_tenant(invoice_id, tenant_id)
    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    if invoice.status in (InvoiceStatus.PAID, InvoiceStatus.CANCELLED):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot cancel invoice with status: {invoice.status.value}",
        )

    invoice = await repos.invoices.update(
        invoice_id,
        InvoiceUpdate(status=InvoiceStatus.CANCELLED),
    )
    return _invoice_to_response(invoice)


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_id: UUID,
    tenant_id: CurrentTenantId,
    user: ManagerUser,
    repos: Repos,
):
    """Delete a draft invoice."""
    invoice = await repos.invoices.get_by_id_for_tenant(invoice_id, tenant_id)
    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    if invoice.status != InvoiceStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Can only delete draft invoices",
        )

    await repos.invoices.delete(invoice_id)
