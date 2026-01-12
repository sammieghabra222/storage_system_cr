"""Payment management endpoints."""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.dependencies import Repos, CurrentUser, ManagerUser, CurrentTenantId
from app.domain.models import (
    Payment,
    PaymentCreate,
    PaymentConfirm,
    PaymentMethod,
    PaymentStatus,
    InvoiceUpdate,
    InvoiceStatus,
)

router = APIRouter()


class PaymentResponse(BaseModel):
    """Payment response schema."""

    id: str
    payment_number: str
    customer_id: str
    invoice_id: str | None
    method: str
    status: str
    amount: Decimal
    currency: str
    payment_date: datetime
    confirmed_at: datetime | None
    confirmed_by: str | None
    reference_number: str | None
    transaction_id: str | None
    sinpe_phone: str | None
    sinpe_confirmation: str | None
    card_last_four: str | None
    card_brand: str | None
    processing_fee: Decimal
    net_amount: Decimal
    notes: str | None

    class Config:
        from_attributes = True


class PaymentListResponse(BaseModel):
    """Paginated list of payments."""

    items: List[PaymentResponse]
    total: int
    skip: int
    limit: int


class PaymentSummary(BaseModel):
    """Payment summary statistics."""

    total_payments: int
    total_amount: Decimal
    pending_count: int
    pending_amount: Decimal
    confirmed_count: int
    confirmed_amount: Decimal
    by_method: dict


class SinpePaymentRequest(BaseModel):
    """Request to record a SINPE payment."""

    customer_id: UUID
    invoice_id: Optional[UUID] = None
    amount: Decimal
    sinpe_phone: Optional[str] = None
    sinpe_confirmation: Optional[str] = None
    notes: Optional[str] = None


def _payment_to_response(payment: Payment) -> PaymentResponse:
    """Convert payment model to response."""
    return PaymentResponse(
        id=str(payment.id),
        payment_number=payment.payment_number,
        customer_id=str(payment.customer_id),
        invoice_id=str(payment.invoice_id) if payment.invoice_id else None,
        method=payment.method.value,
        status=payment.status.value,
        amount=payment.amount,
        currency=payment.currency,
        payment_date=payment.payment_date,
        confirmed_at=payment.confirmed_at,
        confirmed_by=str(payment.confirmed_by) if payment.confirmed_by else None,
        reference_number=payment.reference_number,
        transaction_id=payment.transaction_id,
        sinpe_phone=payment.sinpe_phone,
        sinpe_confirmation=payment.sinpe_confirmation,
        card_last_four=payment.card_last_four,
        card_brand=payment.card_brand,
        processing_fee=payment.processing_fee,
        net_amount=payment.calculated_net_amount,
        notes=payment.notes,
    )


@router.get("", response_model=PaymentListResponse)
async def list_payments(
    tenant_id: CurrentTenantId,
    user: CurrentUser,
    repos: Repos,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None),
    customer_id: Optional[UUID] = Query(None),
    invoice_id: Optional[UUID] = Query(None),
    pending_only: bool = Query(False),
):
    """List payments with optional filters."""
    if pending_only:
        payments = await repos.payments.get_pending(tenant_id)
    elif customer_id:
        payments = await repos.payments.get_by_customer(customer_id, tenant_id)
    elif invoice_id:
        payments = await repos.payments.get_by_invoice(invoice_id, tenant_id)
    else:
        payments = await repos.payments.get_all_for_tenant(tenant_id, skip=skip, limit=limit)

    total = await repos.payments.count_for_tenant(tenant_id)

    return PaymentListResponse(
        items=[_payment_to_response(p) for p in payments],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/summary", response_model=PaymentSummary)
async def get_payment_summary(
    tenant_id: CurrentTenantId,
    user: CurrentUser,
    repos: Repos,
):
    """Get payment summary statistics."""
    all_payments = await repos.payments.get_all_for_tenant(tenant_id, skip=0, limit=10000)
    pending = [p for p in all_payments if p.status == PaymentStatus.PENDING]
    confirmed = [p for p in all_payments if p.status == PaymentStatus.CONFIRMED]

    # Group by method
    by_method = {}
    for payment in confirmed:
        method = payment.method.value
        if method not in by_method:
            by_method[method] = {"count": 0, "amount": Decimal("0")}
        by_method[method]["count"] += 1
        by_method[method]["amount"] += payment.amount

    return PaymentSummary(
        total_payments=len(all_payments),
        total_amount=sum(p.amount for p in confirmed),
        pending_count=len(pending),
        pending_amount=sum(p.amount for p in pending),
        confirmed_count=len(confirmed),
        confirmed_amount=sum(p.amount for p in confirmed),
        by_method=by_method,
    )


@router.get("/pending", response_model=List[PaymentResponse])
async def list_pending_payments(
    tenant_id: CurrentTenantId,
    user: CurrentUser,
    repos: Repos,
):
    """List all pending payments awaiting confirmation."""
    payments = await repos.payments.get_pending(tenant_id)
    return [_payment_to_response(p) for p in payments]


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: UUID,
    tenant_id: CurrentTenantId,
    user: CurrentUser,
    repos: Repos,
):
    """Get a specific payment."""
    payment = await repos.payments.get_by_id_for_tenant(payment_id, tenant_id)

    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )

    return _payment_to_response(payment)


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def record_payment(
    payment_data: PaymentCreate,
    tenant_id: CurrentTenantId,
    user: ManagerUser,
    repos: Repos,
):
    """Record a new payment."""
    # Verify customer exists
    customer = await repos.customers.get_by_id_for_tenant(payment_data.customer_id, tenant_id)
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    # Verify invoice if provided
    if payment_data.invoice_id:
        invoice = await repos.invoices.get_by_id_for_tenant(payment_data.invoice_id, tenant_id)
        if invoice is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found",
            )

    payment = await repos.payments.create_for_tenant(tenant_id, payment_data)
    return _payment_to_response(payment)


@router.post("/sinpe", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def record_sinpe_payment(
    request: SinpePaymentRequest,
    tenant_id: CurrentTenantId,
    user: ManagerUser,
    repos: Repos,
):
    """Record a SINPE/SINPE Móvil payment (awaiting confirmation)."""
    # Verify customer exists
    customer = await repos.customers.get_by_id_for_tenant(request.customer_id, tenant_id)
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    # Determine method
    method = PaymentMethod.SINPE_MOVIL if request.sinpe_phone else PaymentMethod.SINPE

    payment_data = PaymentCreate(
        customer_id=request.customer_id,
        invoice_id=request.invoice_id,
        method=method,
        amount=request.amount,
        sinpe_phone=request.sinpe_phone,
        sinpe_confirmation=request.sinpe_confirmation,
        notes=request.notes,
    )

    payment = await repos.payments.create_for_tenant(tenant_id, payment_data)
    return _payment_to_response(payment)


@router.post("/{payment_id}/confirm", response_model=PaymentResponse)
async def confirm_payment(
    payment_id: UUID,
    confirm_data: PaymentConfirm,
    tenant_id: CurrentTenantId,
    user: ManagerUser,
    repos: Repos,
):
    """Confirm a pending payment."""
    payment = await repos.payments.get_by_id_for_tenant(payment_id, tenant_id)
    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )

    if payment.status != PaymentStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Payment is not pending (status: {payment.status.value})",
        )

    # Update payment
    payment.status = PaymentStatus.CONFIRMED
    payment.confirmed_at = datetime.utcnow()
    payment.confirmed_by = user.id
    if confirm_data.reference_number:
        payment.reference_number = confirm_data.reference_number
    if confirm_data.sinpe_confirmation:
        payment.sinpe_confirmation = confirm_data.sinpe_confirmation
    if confirm_data.notes:
        payment.notes = (payment.notes or "") + f"\nConfirmation: {confirm_data.notes}"

    payment.updated_at = datetime.utcnow()

    # If linked to invoice, update invoice
    if payment.invoice_id:
        invoice = await repos.invoices.get_by_id(payment.invoice_id)
        if invoice:
            new_amount_paid = invoice.amount_paid + payment.amount
            new_status = invoice.status
            if new_amount_paid >= invoice.total:
                new_status = InvoiceStatus.PAID
            elif new_amount_paid > 0:
                new_status = InvoiceStatus.PARTIAL

            await repos.invoices.update(
                invoice.id,
                InvoiceUpdate(amount_paid=new_amount_paid, status=new_status),
            )

    return _payment_to_response(payment)


@router.post("/{payment_id}/reject", response_model=PaymentResponse)
async def reject_payment(
    payment_id: UUID,
    tenant_id: CurrentTenantId,
    user: ManagerUser,
    repos: Repos,
    reason: str = Query(None, max_length=500),
):
    """Reject/fail a pending payment."""
    payment = await repos.payments.get_by_id_for_tenant(payment_id, tenant_id)
    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )

    if payment.status != PaymentStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Payment is not pending (status: {payment.status.value})",
        )

    payment.status = PaymentStatus.FAILED
    payment.updated_at = datetime.utcnow()
    if reason:
        payment.notes = (payment.notes or "") + f"\nRejected: {reason}"

    return _payment_to_response(payment)


# SINPE QR Code endpoints

class SinpeQRRequest(BaseModel):
    """Request for SINPE QR code generation."""

    amount: Decimal
    invoice_id: Optional[UUID] = None
    description: Optional[str] = None


class SinpeQRResponse(BaseModel):
    """Response with SINPE QR code data."""

    qr_data: str
    phone_number: str
    recipient_name: str
    amount: Optional[float]
    currency: str
    description: Optional[str]
    invoice_number: Optional[str]
    qr_base64: Optional[str] = None


@router.post("/sinpe/qr", response_model=SinpeQRResponse)
async def generate_sinpe_qr(
    request: SinpeQRRequest,
    tenant_id: CurrentTenantId,
    user: CurrentUser,
    repos: Repos,
):
    """
    Generate a SINPE QR code for payment.

    The QR code can be scanned by banking apps to pre-fill payment details.
    """
    from app.infrastructure.integrations.sinpe.qr_generator import (
        get_sinpe_qr_generator,
        SinpeQRData,
    )

    # Get tenant info for SINPE number
    tenant = await repos.tenants.get_by_id(tenant_id)
    if not tenant or not tenant.sinpe_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant SINPE number not configured. Please set up your SINPE number in settings.",
        )

    # Get invoice info if provided
    invoice_number = None
    if request.invoice_id:
        invoice = await repos.invoices.get_by_id_for_tenant(request.invoice_id, tenant_id)
        if invoice:
            invoice_number = invoice.invoice_number

    # Generate QR code
    generator = get_sinpe_qr_generator()
    result = generator.generate_payment_qr(
        phone_number=tenant.sinpe_number,
        recipient_name=tenant.name,
        amount=request.amount,
        invoice_number=invoice_number,
        description=request.description,
    )

    # Handle both generator types
    if hasattr(result, 'qr_data'):
        # SinpeQRResult from full generator
        return SinpeQRResponse(
            qr_data=result.qr_data,
            phone_number=result.phone_number,
            recipient_name=tenant.name,
            amount=float(result.amount) if result.amount else None,
            currency="CRC",
            description=result.description,
            invoice_number=invoice_number,
            qr_base64=result.qr_base64 if hasattr(result, 'qr_base64') else None,
        )
    else:
        # Dict from simple generator
        return SinpeQRResponse(
            qr_data=result["qr_data"],
            phone_number=result["phone_number"],
            recipient_name=result["recipient_name"],
            amount=result["amount"],
            currency=result["currency"],
            description=result["description"],
            invoice_number=result["invoice_number"],
        )


@router.get("/sinpe/qr/invoice/{invoice_id}", response_model=SinpeQRResponse)
async def generate_invoice_qr(
    invoice_id: UUID,
    tenant_id: CurrentTenantId,
    user: CurrentUser,
    repos: Repos,
):
    """
    Generate a SINPE QR code for a specific invoice.

    Uses the invoice balance due as the payment amount.
    """
    from app.infrastructure.integrations.sinpe.qr_generator import get_sinpe_qr_generator

    # Get tenant info
    tenant = await repos.tenants.get_by_id(tenant_id)
    if not tenant or not tenant.sinpe_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant SINPE number not configured",
        )

    # Get invoice
    invoice = await repos.invoices.get_by_id_for_tenant(invoice_id, tenant_id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    # Calculate balance due
    balance_due = invoice.balance_due

    if balance_due <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invoice has no balance due",
        )

    # Generate QR code
    generator = get_sinpe_qr_generator()
    result = generator.generate_payment_qr(
        phone_number=tenant.sinpe_number,
        recipient_name=tenant.name,
        amount=balance_due,
        invoice_number=invoice.invoice_number,
        description=f"Pago factura {invoice.invoice_number}",
    )

    if hasattr(result, 'qr_data'):
        return SinpeQRResponse(
            qr_data=result.qr_data,
            phone_number=result.phone_number,
            recipient_name=tenant.name,
            amount=float(result.amount) if result.amount else None,
            currency="CRC",
            description=result.description,
            invoice_number=invoice.invoice_number,
            qr_base64=result.qr_base64 if hasattr(result, 'qr_base64') else None,
        )
    else:
        return SinpeQRResponse(
            qr_data=result["qr_data"],
            phone_number=result["phone_number"],
            recipient_name=result["recipient_name"],
            amount=result["amount"],
            currency=result["currency"],
            description=result["description"],
            invoice_number=result["invoice_number"],
        )


# Credit Card Payment Endpoints

class CardPaymentIntentRequest(BaseModel):
    """Request to create a card payment intent."""

    customer_id: UUID
    invoice_id: Optional[UUID] = None
    amount: Decimal
    currency: str = "CRC"
    description: Optional[str] = None


class CardPaymentIntentResponse(BaseModel):
    """Response with payment intent details."""

    intent_id: str
    client_secret: Optional[str]
    status: str
    amount: Decimal
    currency: str


class CardPaymentConfirmRequest(BaseModel):
    """Request to confirm a card payment."""

    intent_id: str
    payment_method_id: Optional[str] = None


class CardPaymentStatusResponse(BaseModel):
    """Response with payment status."""

    intent_id: str
    status: str
    success: bool
    transaction_id: Optional[str] = None
    card_brand: Optional[str] = None
    card_last_four: Optional[str] = None
    amount_captured: Optional[Decimal] = None
    processing_fee: Optional[Decimal] = None
    error_message: Optional[str] = None


class CardRefundRequest(BaseModel):
    """Request to refund a card payment."""

    transaction_id: str
    amount: Optional[Decimal] = None
    reason: Optional[str] = None


class CardRefundResponse(BaseModel):
    """Response for refund request."""

    success: bool
    refund_id: Optional[str] = None
    amount_refunded: Decimal
    status: str
    error_message: Optional[str] = None


@router.post("/card/intent", response_model=CardPaymentIntentResponse)
async def create_card_payment_intent(
    request: CardPaymentIntentRequest,
    tenant_id: CurrentTenantId,
    user: CurrentUser,
    repos: Repos,
):
    """
    Create a payment intent for card payment.

    Returns a client_secret that should be used with Stripe Elements
    on the frontend to collect card details securely.
    """
    from app.infrastructure.integrations.card_processor import (
        get_card_processor,
        CardPaymentIntent,
    )

    # Verify customer exists
    customer = await repos.customers.get_by_id_for_tenant(request.customer_id, tenant_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    # Verify invoice if provided
    if request.invoice_id:
        invoice = await repos.invoices.get_by_id_for_tenant(request.invoice_id, tenant_id)
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found",
            )

    # Create payment intent
    processor = get_card_processor()
    payment_intent = CardPaymentIntent(
        amount=request.amount,
        currency=request.currency,
        customer_id=request.customer_id,
        invoice_id=request.invoice_id,
        description=request.description or f"Pago Bodega - {customer.full_name}",
        customer_email=customer.email,
        customer_name=customer.full_name,
        metadata={
            "tenant_id": str(tenant_id),
        },
    )

    result = await processor.create_payment_intent(payment_intent)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error_message or "Failed to create payment intent",
        )

    return CardPaymentIntentResponse(
        intent_id=result.intent_id,
        client_secret=result.client_secret,
        status=result.status.value,
        amount=request.amount,
        currency=request.currency,
    )


@router.post("/card/confirm", response_model=CardPaymentStatusResponse)
async def confirm_card_payment(
    request: CardPaymentConfirmRequest,
    tenant_id: CurrentTenantId,
    user: ManagerUser,
    repos: Repos,
):
    """
    Confirm a card payment after card details collected on frontend.

    This is typically called after Stripe.js confirms the payment.
    """
    from app.infrastructure.integrations.card_processor import get_card_processor

    processor = get_card_processor()
    result = await processor.confirm_payment(
        request.intent_id,
        request.payment_method_id,
    )

    # If successful, record the payment
    if result.success and result.transaction_id:
        # Create payment record
        payment_data = PaymentCreate(
            customer_id=UUID(result.card_details.cardholder_name) if result.card_details else None,
            method=PaymentMethod.CREDIT_CARD,
            amount=result.amount_captured or Decimal("0"),
            currency="CRC",
        )

        # Note: In production, extract customer_id from the payment intent metadata
        # For now, just return the status

    return CardPaymentStatusResponse(
        intent_id=result.intent_id,
        status=result.status.value,
        success=result.success,
        transaction_id=result.transaction_id,
        card_brand=result.card_details.brand.value if result.card_details else None,
        card_last_four=result.card_details.last_four if result.card_details else None,
        amount_captured=result.amount_captured,
        processing_fee=result.processing_fee,
        error_message=result.error_message,
    )


@router.get("/card/status/{intent_id}", response_model=CardPaymentStatusResponse)
async def get_card_payment_status(
    intent_id: str,
    tenant_id: CurrentTenantId,
    user: CurrentUser,
):
    """Get the current status of a card payment intent."""
    from app.infrastructure.integrations.card_processor import get_card_processor

    processor = get_card_processor()
    result = await processor.get_payment_status(intent_id)

    return CardPaymentStatusResponse(
        intent_id=result.intent_id,
        status=result.status.value,
        success=result.success,
        transaction_id=result.transaction_id,
        card_brand=result.card_details.brand.value if result.card_details else None,
        card_last_four=result.card_details.last_four if result.card_details else None,
        amount_captured=result.amount_captured,
        processing_fee=result.processing_fee,
        error_message=result.error_message,
    )


@router.post("/card/refund", response_model=CardRefundResponse)
async def refund_card_payment(
    request: CardRefundRequest,
    tenant_id: CurrentTenantId,
    user: ManagerUser,
):
    """
    Refund a completed card payment.

    If amount is not specified, performs a full refund.
    """
    from app.infrastructure.integrations.card_processor import (
        get_card_processor,
        CardRefundRequest as ProcessorRefundRequest,
    )

    processor = get_card_processor()
    refund_request = ProcessorRefundRequest(
        transaction_id=request.transaction_id,
        amount=request.amount,
        reason=request.reason,
    )

    result = await processor.refund_payment(refund_request)

    return CardRefundResponse(
        success=result.success,
        refund_id=result.refund_id if result.success else None,
        amount_refunded=result.amount_refunded,
        status=result.status,
        error_message=result.error_message,
    )


@router.post("/card/cancel/{intent_id}", response_model=CardPaymentStatusResponse)
async def cancel_card_payment(
    intent_id: str,
    tenant_id: CurrentTenantId,
    user: ManagerUser,
):
    """Cancel a pending card payment intent."""
    from app.infrastructure.integrations.card_processor import get_card_processor

    processor = get_card_processor()
    result = await processor.cancel_payment(intent_id)

    return CardPaymentStatusResponse(
        intent_id=result.intent_id,
        status=result.status.value,
        success=result.success,
        error_message=result.error_message,
    )
