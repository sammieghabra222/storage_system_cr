"""Contract model for rental agreements."""
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.models.base import TenantScopedEntity


class ContractStatus(str, Enum):
    """Contract status."""

    DRAFT = "draft"  # Not yet signed
    ACTIVE = "active"  # Currently in effect
    EXPIRED = "expired"  # Past end date, not renewed
    TERMINATED = "terminated"  # Ended early
    SUSPENDED = "suspended"  # Temporarily suspended (e.g., non-payment)


class BillingCycle(str, Enum):
    """Billing frequency."""

    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMI_ANNUAL = "semi_annual"
    ANNUAL = "annual"


class Contract(TenantScopedEntity):
    """Rental contract/agreement model."""

    # References
    customer_id: UUID = Field(..., description="Customer renting the unit")
    unit_id: UUID = Field(..., description="Storage unit being rented")

    # Contract details
    contract_number: str = Field(..., max_length=50, description="Unique contract identifier")
    status: ContractStatus = Field(default=ContractStatus.DRAFT)

    # Dates
    start_date: date = Field(..., description="Contract start date")
    end_date: Optional[date] = Field(None, description="Contract end date (null = month-to-month)")
    signed_date: Optional[date] = Field(None, description="Date contract was signed")
    move_in_date: Optional[date] = Field(None, description="Actual move-in date")
    move_out_date: Optional[date] = Field(None, description="Actual move-out date")

    # Billing
    monthly_rate: Decimal = Field(..., ge=0, description="Monthly rent amount")
    deposit_amount: Decimal = Field(default=Decimal("0"), ge=0, description="Security deposit")
    deposit_paid: bool = Field(default=False)
    deposit_returned: bool = Field(default=False)
    deposit_return_date: Optional[date] = None

    billing_cycle: BillingCycle = Field(default=BillingCycle.MONTHLY)
    billing_day: int = Field(default=1, ge=1, le=28, description="Day of month for billing")
    grace_period_days: int = Field(default=5, ge=0, description="Days after due date before late fee")
    late_fee_amount: Decimal = Field(default=Decimal("0"), ge=0)
    late_fee_percent: Optional[Decimal] = Field(None, ge=0, le=100, description="Late fee as percentage")

    # Auto-renewal
    auto_renew: bool = Field(default=True)
    renewal_notice_days: int = Field(default=30, description="Days before end to send renewal notice")

    # Pricing adjustments
    discount_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    discount_reason: Optional[str] = Field(None, max_length=255)

    # Insurance
    requires_insurance: bool = Field(default=False)
    insurance_provider: Optional[str] = Field(None, max_length=255)
    insurance_policy_number: Optional[str] = Field(None, max_length=100)

    # Access
    access_code: Optional[str] = Field(None, max_length=50, description="Gate/door access code")
    access_hours: Optional[str] = Field(None, max_length=100, description="e.g., '24/7' or '6am-10pm'")

    # Notes
    terms_accepted: bool = Field(default=False)
    special_terms: Optional[str] = Field(None, max_length=2000)
    internal_notes: Optional[str] = Field(None, max_length=2000)

    @property
    def is_month_to_month(self) -> bool:
        """Check if contract is month-to-month (no end date)."""
        return self.end_date is None

    @property
    def effective_monthly_rate(self) -> Decimal:
        """Calculate rate after discount."""
        if self.discount_percent:
            discount = self.monthly_rate * (self.discount_percent / 100)
            return self.monthly_rate - discount
        return self.monthly_rate


class ContractCreate(BaseModel):
    """Schema for creating a contract."""

    customer_id: UUID
    unit_id: UUID
    contract_number: Optional[str] = Field(None, max_length=50)
    start_date: date
    end_date: Optional[date] = None
    monthly_rate: Decimal = Field(..., ge=0)
    deposit_amount: Decimal = Field(default=Decimal("0"), ge=0)
    billing_cycle: BillingCycle = Field(default=BillingCycle.MONTHLY)
    billing_day: int = Field(default=1, ge=1, le=28)
    grace_period_days: int = Field(default=5, ge=0)
    late_fee_amount: Decimal = Field(default=Decimal("0"), ge=0)
    late_fee_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    auto_renew: bool = Field(default=True)
    discount_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    discount_reason: Optional[str] = Field(None, max_length=255)
    requires_insurance: bool = Field(default=False)
    access_code: Optional[str] = Field(None, max_length=50)
    access_hours: Optional[str] = Field(None, max_length=100)
    special_terms: Optional[str] = Field(None, max_length=2000)
    internal_notes: Optional[str] = Field(None, max_length=2000)


class ContractUpdate(BaseModel):
    """Schema for updating a contract."""

    status: Optional[ContractStatus] = None
    end_date: Optional[date] = None
    signed_date: Optional[date] = None
    move_in_date: Optional[date] = None
    move_out_date: Optional[date] = None
    monthly_rate: Optional[Decimal] = Field(None, ge=0)
    deposit_amount: Optional[Decimal] = Field(None, ge=0)
    deposit_paid: Optional[bool] = None
    deposit_returned: Optional[bool] = None
    deposit_return_date: Optional[date] = None
    billing_day: Optional[int] = Field(None, ge=1, le=28)
    grace_period_days: Optional[int] = Field(None, ge=0)
    late_fee_amount: Optional[Decimal] = Field(None, ge=0)
    late_fee_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    auto_renew: Optional[bool] = None
    renewal_notice_days: Optional[int] = None
    discount_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    discount_reason: Optional[str] = Field(None, max_length=255)
    requires_insurance: Optional[bool] = None
    insurance_provider: Optional[str] = Field(None, max_length=255)
    insurance_policy_number: Optional[str] = Field(None, max_length=100)
    access_code: Optional[str] = Field(None, max_length=50)
    access_hours: Optional[str] = Field(None, max_length=100)
    terms_accepted: Optional[bool] = None
    special_terms: Optional[str] = Field(None, max_length=2000)
    internal_notes: Optional[str] = Field(None, max_length=2000)
