"""Sandbox card processor for testing.

Simulates card processing without real transactions.
Use test card numbers to simulate different scenarios.
"""

import uuid
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


# Test card numbers and their behaviors
TEST_CARDS = {
    "4242424242424242": {"brand": CardBrand.VISA, "result": "success"},
    "4000000000000002": {"brand": CardBrand.VISA, "result": "decline"},
    "4000000000009995": {"brand": CardBrand.VISA, "result": "insufficient_funds"},
    "4000000000000069": {"brand": CardBrand.VISA, "result": "expired_card"},
    "4000002500003155": {"brand": CardBrand.VISA, "result": "3d_secure"},
    "5555555555554444": {"brand": CardBrand.MASTERCARD, "result": "success"},
    "378282246310005": {"brand": CardBrand.AMEX, "result": "success"},
}


class SandboxCardProcessor(CardProcessor):
    """Sandbox processor for testing card payments.

    Test card numbers:
    - 4242424242424242: Success (Visa)
    - 5555555555554444: Success (Mastercard)
    - 378282246310005: Success (Amex)
    - 4000000000000002: Generic decline
    - 4000000000009995: Insufficient funds
    - 4000000000000069: Expired card
    - 4000002500003155: Requires 3D Secure
    """

    def __init__(self, config: CardProcessorConfig):
        super().__init__(config)
        self._intents: dict[str, dict] = {}
        self._transactions: dict[str, dict] = {}

    async def create_payment_intent(
        self, payment: CardPaymentIntent
    ) -> CardPaymentResult:
        """Create a sandbox payment intent."""
        intent_id = f"pi_sandbox_{uuid.uuid4().hex[:16]}"
        client_secret = f"{intent_id}_secret_{uuid.uuid4().hex[:24]}"

        self._intents[intent_id] = {
            "id": intent_id,
            "amount": payment.amount,
            "currency": payment.currency,
            "customer_id": str(payment.customer_id),
            "invoice_id": str(payment.invoice_id) if payment.invoice_id else None,
            "status": PaymentIntentStatus.REQUIRES_PAYMENT_METHOD,
            "client_secret": client_secret,
            "metadata": payment.metadata,
            "created_at": datetime.utcnow(),
        }

        return CardPaymentResult(
            success=True,
            intent_id=intent_id,
            status=PaymentIntentStatus.REQUIRES_PAYMENT_METHOD,
            client_secret=client_secret,
            created_at=datetime.utcnow(),
        )

    async def confirm_payment(
        self, intent_id: str, payment_method_id: Optional[str] = None
    ) -> CardPaymentResult:
        """Confirm a sandbox payment.

        Use payment_method_id as a test card number to simulate different outcomes.
        """
        if intent_id not in self._intents:
            return CardPaymentResult(
                success=False,
                intent_id=intent_id,
                status=PaymentIntentStatus.FAILED,
                error_code="invalid_intent",
                error_message="Payment intent not found",
            )

        intent = self._intents[intent_id]

        # Default to success card if no payment method specified
        card_number = payment_method_id or "4242424242424242"
        card_config = TEST_CARDS.get(card_number, TEST_CARDS["4242424242424242"])

        result = card_config["result"]

        if result == "success":
            return await self._process_success(intent_id, intent, card_config)
        elif result == "3d_secure":
            return await self._process_3d_secure(intent_id, intent, card_config)
        else:
            return await self._process_decline(intent_id, intent, result)

    async def _process_success(
        self, intent_id: str, intent: dict, card_config: dict
    ) -> CardPaymentResult:
        """Process a successful payment."""
        transaction_id = f"txn_sandbox_{uuid.uuid4().hex[:16]}"
        now = datetime.utcnow()

        # Calculate processing fee (2.9% + $0.30 typical)
        amount = intent["amount"]
        fee = (amount * Decimal("0.029")) + Decimal("0.30")
        net = amount - fee

        # Update intent
        intent["status"] = PaymentIntentStatus.SUCCEEDED
        intent["transaction_id"] = transaction_id
        intent["processed_at"] = now

        # Store transaction
        self._transactions[transaction_id] = {
            "intent_id": intent_id,
            "amount": amount,
            "fee": fee,
            "net": net,
            "status": "captured",
            "created_at": now,
        }

        return CardPaymentResult(
            success=True,
            intent_id=intent_id,
            status=PaymentIntentStatus.SUCCEEDED,
            transaction_id=transaction_id,
            card_details=CardDetails(
                brand=card_config["brand"],
                last_four="4242",
                exp_month=12,
                exp_year=2030,
                cardholder_name="Test User",
            ),
            amount_captured=amount,
            processing_fee=fee,
            net_amount=net,
            processed_at=now,
        )

    async def _process_3d_secure(
        self, intent_id: str, intent: dict, card_config: dict
    ) -> CardPaymentResult:
        """Process a payment requiring 3D Secure."""
        intent["status"] = PaymentIntentStatus.REQUIRES_ACTION

        return CardPaymentResult(
            success=True,
            intent_id=intent_id,
            status=PaymentIntentStatus.REQUIRES_ACTION,
            client_secret=intent["client_secret"],
            redirect_url=f"https://sandbox.3dsecure.test/auth/{intent_id}",
        )

    async def _process_decline(
        self, intent_id: str, intent: dict, reason: str
    ) -> CardPaymentResult:
        """Process a declined payment."""
        intent["status"] = PaymentIntentStatus.FAILED

        error_messages = {
            "decline": "La tarjeta fue rechazada",
            "insufficient_funds": "Fondos insuficientes",
            "expired_card": "Tarjeta expirada",
        }

        return CardPaymentResult(
            success=False,
            intent_id=intent_id,
            status=PaymentIntentStatus.FAILED,
            error_code=reason,
            error_message=error_messages.get(reason, "Pago rechazado"),
            decline_code=reason,
        )

    async def capture_payment(self, intent_id: str) -> CardPaymentResult:
        """Capture an authorized sandbox payment."""
        if intent_id not in self._intents:
            return CardPaymentResult(
                success=False,
                intent_id=intent_id,
                status=PaymentIntentStatus.FAILED,
                error_code="invalid_intent",
                error_message="Payment intent not found",
            )

        intent = self._intents[intent_id]
        if intent["status"] != PaymentIntentStatus.REQUIRES_CONFIRMATION:
            return CardPaymentResult(
                success=False,
                intent_id=intent_id,
                status=intent["status"],
                error_code="invalid_status",
                error_message="Payment cannot be captured in current status",
            )

        return await self._process_success(
            intent_id,
            intent,
            {"brand": CardBrand.VISA},
        )

    async def cancel_payment(self, intent_id: str) -> CardPaymentResult:
        """Cancel a sandbox payment intent."""
        if intent_id not in self._intents:
            return CardPaymentResult(
                success=False,
                intent_id=intent_id,
                status=PaymentIntentStatus.FAILED,
                error_code="invalid_intent",
                error_message="Payment intent not found",
            )

        intent = self._intents[intent_id]
        intent["status"] = PaymentIntentStatus.CANCELLED

        return CardPaymentResult(
            success=True,
            intent_id=intent_id,
            status=PaymentIntentStatus.CANCELLED,
        )

    async def refund_payment(self, request: CardRefundRequest) -> CardRefundResult:
        """Refund a sandbox payment."""
        if request.transaction_id not in self._transactions:
            return CardRefundResult(
                success=False,
                refund_id="",
                amount_refunded=Decimal("0"),
                status="failed",
                error_message="Transaction not found",
            )

        transaction = self._transactions[request.transaction_id]
        refund_amount = request.amount or transaction["amount"]

        if refund_amount > transaction["amount"]:
            return CardRefundResult(
                success=False,
                refund_id="",
                amount_refunded=Decimal("0"),
                status="failed",
                error_message="Refund amount exceeds transaction amount",
            )

        refund_id = f"re_sandbox_{uuid.uuid4().hex[:16]}"

        return CardRefundResult(
            success=True,
            refund_id=refund_id,
            amount_refunded=refund_amount,
            status="succeeded",
        )

    async def get_payment_status(self, intent_id: str) -> CardPaymentResult:
        """Get sandbox payment status."""
        if intent_id not in self._intents:
            return CardPaymentResult(
                success=False,
                intent_id=intent_id,
                status=PaymentIntentStatus.FAILED,
                error_code="invalid_intent",
                error_message="Payment intent not found",
            )

        intent = self._intents[intent_id]

        return CardPaymentResult(
            success=intent["status"] == PaymentIntentStatus.SUCCEEDED,
            intent_id=intent_id,
            status=intent["status"],
            transaction_id=intent.get("transaction_id"),
            created_at=intent["created_at"],
            processed_at=intent.get("processed_at"),
        )

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify sandbox webhook (always returns True in sandbox)."""
        return True
