"""Base card processor interface and models.

Provides a provider-agnostic interface for credit card processing.
Supports multiple providers: Stripe, BAC Credomatic, etc.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CardProcessorProvider(str, Enum):
    """Supported card processor providers."""

    STRIPE = "stripe"
    BAC_CREDOMATIC = "bac_credomatic"
    SANDBOX = "sandbox"  # For testing


class PaymentIntentStatus(str, Enum):
    """Status of a payment intent."""

    REQUIRES_PAYMENT_METHOD = "requires_payment_method"
    REQUIRES_CONFIRMATION = "requires_confirmation"
    REQUIRES_ACTION = "requires_action"  # 3D Secure, etc.
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CardBrand(str, Enum):
    """Credit card brands."""

    VISA = "visa"
    MASTERCARD = "mastercard"
    AMEX = "amex"
    DISCOVER = "discover"
    DINERS = "diners"
    JCB = "jcb"
    UNKNOWN = "unknown"


class CardProcessorConfig(BaseModel):
    """Configuration for card processor."""

    provider: CardProcessorProvider = CardProcessorProvider.SANDBOX
    api_key: Optional[str] = None
    secret_key: Optional[str] = None
    webhook_secret: Optional[str] = None
    sandbox_mode: bool = True
    currency: str = "CRC"

    # Costa Rica specific
    merchant_id: Optional[str] = None
    terminal_id: Optional[str] = None


class CardDetails(BaseModel):
    """Card details for display (never store full numbers)."""

    brand: CardBrand = CardBrand.UNKNOWN
    last_four: str = Field(..., max_length=4)
    exp_month: int = Field(..., ge=1, le=12)
    exp_year: int = Field(..., ge=2024)
    cardholder_name: Optional[str] = None
    country: Optional[str] = None


class CardPaymentIntent(BaseModel):
    """Request to create a payment intent."""

    amount: Decimal = Field(..., ge=Decimal("0.01"))
    currency: str = Field(default="CRC", max_length=3)
    customer_id: UUID
    invoice_id: Optional[UUID] = None
    description: Optional[str] = None

    # Customer info for fraud prevention
    customer_email: Optional[str] = None
    customer_name: Optional[str] = None

    # Metadata
    metadata: dict = Field(default_factory=dict)


class CardPaymentResult(BaseModel):
    """Result of a card payment attempt."""

    success: bool
    intent_id: str = Field(..., description="Provider's payment intent ID")
    status: PaymentIntentStatus

    # On success
    transaction_id: Optional[str] = None
    card_details: Optional[CardDetails] = None
    amount_captured: Optional[Decimal] = None
    processing_fee: Optional[Decimal] = None
    net_amount: Optional[Decimal] = None

    # For 3D Secure
    client_secret: Optional[str] = Field(None, description="For frontend to complete payment")
    redirect_url: Optional[str] = Field(None, description="3D Secure redirect")

    # On failure
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    decline_code: Optional[str] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None


class CardRefundRequest(BaseModel):
    """Request to refund a card payment."""

    transaction_id: str
    amount: Optional[Decimal] = None  # None = full refund
    reason: Optional[str] = None


class CardRefundResult(BaseModel):
    """Result of a refund attempt."""

    success: bool
    refund_id: str
    amount_refunded: Decimal
    status: str
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CardProcessor(ABC):
    """Abstract base class for card processors."""

    def __init__(self, config: CardProcessorConfig):
        self.config = config

    @abstractmethod
    async def create_payment_intent(
        self, payment: CardPaymentIntent
    ) -> CardPaymentResult:
        """Create a payment intent for the given amount."""
        pass

    @abstractmethod
    async def confirm_payment(
        self, intent_id: str, payment_method_id: Optional[str] = None
    ) -> CardPaymentResult:
        """Confirm a payment intent."""
        pass

    @abstractmethod
    async def capture_payment(self, intent_id: str) -> CardPaymentResult:
        """Capture an authorized payment."""
        pass

    @abstractmethod
    async def cancel_payment(self, intent_id: str) -> CardPaymentResult:
        """Cancel a payment intent."""
        pass

    @abstractmethod
    async def refund_payment(self, request: CardRefundRequest) -> CardRefundResult:
        """Refund a completed payment."""
        pass

    @abstractmethod
    async def get_payment_status(self, intent_id: str) -> CardPaymentResult:
        """Get the current status of a payment intent."""
        pass

    @abstractmethod
    def verify_webhook_signature(
        self, payload: bytes, signature: str
    ) -> bool:
        """Verify webhook signature from the provider."""
        pass


def get_card_processor(config: Optional[CardProcessorConfig] = None) -> CardProcessor:
    """Factory function to get the appropriate card processor."""
    if config is None:
        config = CardProcessorConfig()

    if config.provider == CardProcessorProvider.STRIPE:
        from app.infrastructure.integrations.card_processor.stripe_processor import (
            StripeCardProcessor,
        )
        return StripeCardProcessor(config)

    elif config.provider == CardProcessorProvider.BAC_CREDOMATIC:
        from app.infrastructure.integrations.card_processor.bac_processor import (
            BACCardProcessor,
        )
        return BACCardProcessor(config)

    else:
        # Default to sandbox
        from app.infrastructure.integrations.card_processor.sandbox_processor import (
            SandboxCardProcessor,
        )
        return SandboxCardProcessor(config)
