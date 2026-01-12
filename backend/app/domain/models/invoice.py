"""Invoice model for billing."""
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.models.base import TenantScopedEntity


class InvoiceStatus(str, Enum):
    """Invoice status."""

    DRAFT = "draft"  # Not yet sent
    SENT = "sent"  # Sent to customer
    VIEWED = "viewed"  # Customer has viewed
    PARTIAL = "partial"  # Partially paid
    PAID = "paid"  # Fully paid
    OVERDUE = "overdue"  # Past due date, unpaid
    CANCELLED = "cancelled"  # Voided
    REFUNDED = "refunded"  # Payment returned


class InvoiceLineItem(BaseModel):
    """Line item on an invoice."""

    description: str = Field(..., max_length=500)
    quantity: Decimal = Field(default=Decimal("1"), ge=0)
    unit_price: Decimal = Field(..., ge=0)
    tax_rate: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    discount_percent: Decimal = Field(default=Decimal("0"), ge=0, le=100)

    @property
    def subtotal(self) -> Decimal:
        """Calculate line subtotal before tax."""
        gross = self.quantity * self.unit_price
        if self.discount_percent:
            discount = gross * (self.discount_percent / 100)
            return gross - discount
        return gross

    @property
    def tax_amount(self) -> Decimal:
        """Calculate tax for this line."""
        return self.subtotal * (self.tax_rate / 100)

    @property
    def total(self) -> Decimal:
        """Calculate line total including tax."""
        return self.subtotal + self.tax_amount


class Invoice(TenantScopedEntity):
    """Invoice model."""

    # References
    customer_id: UUID = Field(..., description="Customer being billed")
    contract_id: Optional[UUID] = Field(None, description="Related contract")

    # Invoice details
    invoice_number: str = Field(..., max_length=50, description="Unique invoice number")
    status: InvoiceStatus = Field(default=InvoiceStatus.DRAFT)

    # Dates
    issue_date: date = Field(default_factory=date.today)
    due_date: date = Field(...)
    period_start: Optional[date] = Field(None, description="Billing period start")
    period_end: Optional[date] = Field(None, description="Billing period end")

    # Line items
    line_items: List[InvoiceLineItem] = Field(default_factory=list)

    # Totals (stored for performance, calculated from line items)
    subtotal: Decimal = Field(default=Decimal("0"), ge=0)
    tax_total: Decimal = Field(default=Decimal("0"), ge=0)
    discount_total: Decimal = Field(default=Decimal("0"), ge=0)
    total: Decimal = Field(default=Decimal("0"), ge=0)

    # Payments
    amount_paid: Decimal = Field(default=Decimal("0"), ge=0)
    currency: str = Field(default="CRC", max_length=3)

    # Late fees
    late_fee_applied: bool = Field(default=False)
    late_fee_amount: Decimal = Field(default=Decimal("0"), ge=0)

    # E-invoicing (Factura Electrónica)
    hacienda_key: Optional[str] = Field(None, max_length=100, description="Hacienda document key")
    hacienda_status: Optional[str] = Field(None, max_length=50, description="Hacienda response status")
    hacienda_xml: Optional[str] = Field(None, description="Signed XML document")

    # Notes
    notes: Optional[str] = Field(None, max_length=2000, description="Notes visible to customer")
    internal_notes: Optional[str] = Field(None, max_length=2000, description="Internal notes")

    @property
    def balance_due(self) -> Decimal:
        """Calculate remaining balance."""
        return self.total + self.late_fee_amount - self.amount_paid

    @property
    def is_overdue(self) -> bool:
        """Check if invoice is past due."""
        return date.today() > self.due_date and self.balance_due > 0

    def recalculate_totals(self) -> None:
        """Recalculate totals from line items."""
        self.subtotal = sum(item.subtotal for item in self.line_items)
        self.tax_total = sum(item.tax_amount for item in self.line_items)
        self.total = self.subtotal + self.tax_total


class InvoiceCreate(BaseModel):
    """Schema for creating an invoice."""

    customer_id: UUID
    contract_id: Optional[UUID] = None
    invoice_number: Optional[str] = Field(None, max_length=50)
    issue_date: date = Field(default_factory=date.today)
    due_date: date
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    line_items: List[InvoiceLineItem] = Field(default_factory=list)
    currency: str = Field(default="CRC", max_length=3)
    notes: Optional[str] = Field(None, max_length=2000)
    internal_notes: Optional[str] = Field(None, max_length=2000)


class InvoiceUpdate(BaseModel):
    """Schema for updating an invoice."""

    status: Optional[InvoiceStatus] = None
    due_date: Optional[date] = None
    line_items: Optional[List[InvoiceLineItem]] = None
    amount_paid: Optional[Decimal] = Field(None, ge=0)
    late_fee_applied: Optional[bool] = None
    late_fee_amount: Optional[Decimal] = Field(None, ge=0)
    hacienda_key: Optional[str] = Field(None, max_length=100)
    hacienda_status: Optional[str] = Field(None, max_length=50)
    hacienda_xml: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=2000)
    internal_notes: Optional[str] = Field(None, max_length=2000)
