"""Stripe card processor implementation.

Integrates with Stripe for card payment processing.
Supports Stripe Elements on frontend for secure card collection.
"""

import hmac
import hashlib
from datetime import datetime
from decimal import Decimal
from typing import Optional

from app.infrastructure.integrations.card_processor.base import (
    CardProcessor,
    CardProcessorConfig,
    CardPaymentIntent,
    CardPaymentResult,
    CardRefundRequest,
    CardRefundResult,
    CardDetails,
    CardBrand,
    PaymentIntentStatus,
)


# Map Stripe status to internal status
STRIPE_STATUS_MAP = {
    "requires_payment_method": PaymentIntentStatus.REQUIRES_PAYMENT_METHOD,
    "requires_confirmation": PaymentIntentStatus.REQUIRES_CONFIRMATION,
    "requires_action": PaymentIntentStatus.REQUIRES_ACTION,
    "processing": PaymentIntentStatus.PROCESSING,
    "succeeded": PaymentIntentStatus.SUCCEEDED,
    "canceled": PaymentIntentStatus.CANCELLED,
}

# Map Stripe card brand to internal brand
STRIPE_BRAND_MAP = {
    "visa": CardBrand.VISA,
    "mastercard": CardBrand.MASTERCARD,
    "amex": CardBrand.AMEX,
    "discover": CardBrand.DISCOVER,
    "diners": CardBrand.DINERS,
    "jcb": CardBrand.JCB,
}


class StripeCardProcessor(CardProcessor):
    """Stripe payment processor.

    Uses Stripe API for secure card processing.
    Requires stripe Python package: pip install stripe
    """

    def __init__(self, config: CardProcessorConfig):
        super().__init__(config)

        try:
            import stripe
            self.stripe = stripe
        except ImportError:
            raise RuntimeError(
                "stripe package not installed. Run: pip install stripe"
            )

        # Configure Stripe
        self.stripe.api_key = config.secret_key
        self.stripe.api_version = "2024-06-20"

    async def create_payment_intent(
        self, payment: CardPaymentIntent
    ) -> CardPaymentResult:
        """Create a Stripe PaymentIntent."""
        try:
            # Convert amount to smallest currency unit (cents/centimos)
            amount_cents = int(payment.amount * 100)

            # Build metadata
            metadata = {
                "customer_id": str(payment.customer_id),
                **payment.metadata,
            }
            if payment.invoice_id:
                metadata["invoice_id"] = str(payment.invoice_id)

            # Create PaymentIntent
            intent = self.stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=payment.currency.lower(),
                description=payment.description,
                metadata=metadata,
                automatic_payment_methods={"enabled": True},
            )

            status = STRIPE_STATUS_MAP.get(
                intent.status,
                PaymentIntentStatus.REQUIRES_PAYMENT_METHOD,
            )

            return CardPaymentResult(
                success=True,
                intent_id=intent.id,
                status=status,
                client_secret=intent.client_secret,
                created_at=datetime.fromtimestamp(intent.created),
            )

        except self.stripe.error.StripeError as e:
            return CardPaymentResult(
                success=False,
                intent_id="",
                status=PaymentIntentStatus.FAILED,
                error_code=e.code if hasattr(e, "code") else "stripe_error",
                error_message=str(e.user_message) if hasattr(e, "user_message") else str(e),
            )

    async def confirm_payment(
        self, intent_id: str, payment_method_id: Optional[str] = None
    ) -> CardPaymentResult:
        """Confirm a Stripe PaymentIntent."""
        try:
            confirm_params = {}
            if payment_method_id:
                confirm_params["payment_method"] = payment_method_id

            intent = self.stripe.PaymentIntent.confirm(
                intent_id,
                **confirm_params,
            )

            return self._intent_to_result(intent)

        except self.stripe.error.CardError as e:
            return CardPaymentResult(
                success=False,
                intent_id=intent_id,
                status=PaymentIntentStatus.FAILED,
                error_code=e.code,
                error_message=e.user_message,
                decline_code=e.decline_code if hasattr(e, "decline_code") else None,
            )
        except self.stripe.error.StripeError as e:
            return CardPaymentResult(
                success=False,
                intent_id=intent_id,
                status=PaymentIntentStatus.FAILED,
                error_code=e.code if hasattr(e, "code") else "stripe_error",
                error_message=str(e.user_message) if hasattr(e, "user_message") else str(e),
            )

    async def capture_payment(self, intent_id: str) -> CardPaymentResult:
        """Capture a Stripe PaymentIntent."""
        try:
            intent = self.stripe.PaymentIntent.capture(intent_id)
            return self._intent_to_result(intent)

        except self.stripe.error.StripeError as e:
            return CardPaymentResult(
                success=False,
                intent_id=intent_id,
                status=PaymentIntentStatus.FAILED,
                error_code=e.code if hasattr(e, "code") else "stripe_error",
                error_message=str(e),
            )

    async def cancel_payment(self, intent_id: str) -> CardPaymentResult:
        """Cancel a Stripe PaymentIntent."""
        try:
            intent = self.stripe.PaymentIntent.cancel(intent_id)
            return CardPaymentResult(
                success=True,
                intent_id=intent_id,
                status=PaymentIntentStatus.CANCELLED,
            )

        except self.stripe.error.StripeError as e:
            return CardPaymentResult(
                success=False,
                intent_id=intent_id,
                status=PaymentIntentStatus.FAILED,
                error_code=e.code if hasattr(e, "code") else "stripe_error",
                error_message=str(e),
            )

    async def refund_payment(self, request: CardRefundRequest) -> CardRefundResult:
        """Refund a Stripe payment."""
        try:
            refund_params = {
                "payment_intent": request.transaction_id,
            }

            if request.amount:
                refund_params["amount"] = int(request.amount * 100)

            if request.reason:
                # Stripe accepts: duplicate, fraudulent, requested_by_customer
                refund_params["reason"] = "requested_by_customer"
                refund_params["metadata"] = {"reason_detail": request.reason}

            refund = self.stripe.Refund.create(**refund_params)

            return CardRefundResult(
                success=True,
                refund_id=refund.id,
                amount_refunded=Decimal(refund.amount) / 100,
                status=refund.status,
                created_at=datetime.fromtimestamp(refund.created),
            )

        except self.stripe.error.StripeError as e:
            return CardRefundResult(
                success=False,
                refund_id="",
                amount_refunded=Decimal("0"),
                status="failed",
                error_message=str(e),
            )

    async def get_payment_status(self, intent_id: str) -> CardPaymentResult:
        """Get Stripe PaymentIntent status."""
        try:
            intent = self.stripe.PaymentIntent.retrieve(intent_id)
            return self._intent_to_result(intent)

        except self.stripe.error.StripeError as e:
            return CardPaymentResult(
                success=False,
                intent_id=intent_id,
                status=PaymentIntentStatus.FAILED,
                error_code=e.code if hasattr(e, "code") else "stripe_error",
                error_message=str(e),
            )

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Stripe webhook signature."""
        if not self.config.webhook_secret:
            return False

        try:
            self.stripe.Webhook.construct_event(
                payload,
                signature,
                self.config.webhook_secret,
            )
            return True
        except (ValueError, self.stripe.error.SignatureVerificationError):
            return False

    def _intent_to_result(self, intent) -> CardPaymentResult:
        """Convert Stripe PaymentIntent to CardPaymentResult."""
        status = STRIPE_STATUS_MAP.get(
            intent.status,
            PaymentIntentStatus.FAILED,
        )

        # Extract card details if available
        card_details = None
        if intent.payment_method and hasattr(intent.payment_method, "card"):
            card = intent.payment_method.card
            card_details = CardDetails(
                brand=STRIPE_BRAND_MAP.get(card.brand, CardBrand.UNKNOWN),
                last_four=card.last4,
                exp_month=card.exp_month,
                exp_year=card.exp_year,
            )

        # Calculate amounts
        amount = Decimal(intent.amount) / 100 if intent.amount else None
        amount_received = (
            Decimal(intent.amount_received) / 100
            if hasattr(intent, "amount_received") and intent.amount_received
            else None
        )

        # Estimate processing fee (Stripe charges ~2.9% + $0.30)
        processing_fee = None
        net_amount = None
        if amount_received:
            processing_fee = (amount_received * Decimal("0.029")) + Decimal("0.30")
            net_amount = amount_received - processing_fee

        return CardPaymentResult(
            success=status == PaymentIntentStatus.SUCCEEDED,
            intent_id=intent.id,
            status=status,
            transaction_id=intent.id if status == PaymentIntentStatus.SUCCEEDED else None,
            card_details=card_details,
            amount_captured=amount_received,
            processing_fee=processing_fee,
            net_amount=net_amount,
            client_secret=intent.client_secret,
            created_at=datetime.fromtimestamp(intent.created),
            processed_at=(
                datetime.utcnow()
                if status == PaymentIntentStatus.SUCCEEDED
                else None
            ),
        )
