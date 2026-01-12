"""Payment model for tracking transactions."""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.models.base import TenantScopedEntity


class PaymentMethod(str, Enum):
    """Payment methods supported."""

    SINPE = "sinpe"  # SINPE bank transfer
    SINPE_MOVIL = "sinpe_movil"  # SINPE Móvil
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    CASH = "cash"
    CHECK = "check"
    BANK_TRANSFER = "bank_transfer"
    OTHER = "other"


class PaymentStatus(str, Enum):
    """Payment status."""

    PENDING = "pending"  # Awaiting confirmation
    CONFIRMED = "confirmed"  # Payment verified
    FAILED = "failed"  # Payment failed
    REFUNDED = "refunded"  # Payment returned
    CANCELLED = "cancelled"  # Payment cancelled


class Payment(TenantScopedEntity):
    """Payment transaction model."""

    # References
    customer_id: UUID = Field(..., description="Customer who made payment")
    invoice_id: Optional[UUID] = Field(None, description="Invoice this payment applies to")

    # Payment details
    payment_number: str = Field(..., max_length=50, description="Unique payment reference")
    method: PaymentMethod = Field(...)
    status: PaymentStatus = Field(default=PaymentStatus.PENDING)

    # Amount
    amount: Decimal = Field(..., ge=0)
    currency: str = Field(default="CRC", max_length=3)
    exchange_rate: Optional[Decimal] = Field(None, description="If paid in different currency")

    # Dates
    payment_date: datetime = Field(default_factory=datetime.utcnow)
    confirmed_at: Optional[datetime] = None
    confirmed_by: Optional[UUID] = Field(None, description="User who confirmed the payment")

    # Transaction references
    reference_number: Optional[str] = Field(None, max_length=100, description="Bank/SINPE reference")
    transaction_id: Optional[str] = Field(None, max_length=100, description="Gateway transaction ID")

    # SINPE specific
    sinpe_phone: Optional[str] = Field(None, max_length=20, description="SINPE Móvil phone used")
    sinpe_confirmation: Optional[str] = Field(None, max_length=50, description="SINPE confirmation code")

    # Card details (masked)
    card_last_four: Optional[str] = Field(None, max_length=4)
    card_brand: Optional[str] = Field(None, max_length=20)

    # Processing fees (if applicable)
    processing_fee: Decimal = Field(default=Decimal("0"), ge=0)
    net_amount: Optional[Decimal] = Field(None, description="Amount after fees")

    # Notes
    notes: Optional[str] = Field(None, max_length=1000)
    internal_notes: Optional[str] = Field(None, max_length=1000)

    @property
    def calculated_net_amount(self) -> Decimal:
        """Calculate net amount after processing fee."""
        return self.amount - self.processing_fee


class PaymentCreate(BaseModel):
    """Schema for creating/recording a payment."""

    customer_id: UUID
    invoice_id: Optional[UUID] = None
    method: PaymentMethod
    amount: Decimal = Field(..., ge=0)
    currency: str = Field(default="CRC", max_length=3)
    payment_date: Optional[datetime] = None
    reference_number: Optional[str] = Field(None, max_length=100)
    sinpe_phone: Optional[str] = Field(None, max_length=20)
    sinpe_confirmation: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = Field(None, max_length=1000)


class PaymentConfirm(BaseModel):
    """Schema for confirming a payment."""

    reference_number: Optional[str] = Field(None, max_length=100)
    sinpe_confirmation: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = Field(None, max_length=1000)
