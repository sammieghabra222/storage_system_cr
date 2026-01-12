"""Notification service for email and SMS notifications."""
from datetime import date, timedelta
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging

from pydantic import BaseModel, Field

from app.domain.models.customer import Customer
from app.domain.models.invoice import Invoice, InvoiceStatus
from app.domain.models.contract import Contract, ContractStatus
from app.domain.models.payment import Payment, PaymentStatus
from app.infrastructure.repositories.base import (
    CustomerRepository,
    InvoiceRepository,
    ContractRepository,
    TenantRepository,
)

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    """Types of notifications."""

    INVOICE_CREATED = "invoice_created"
    INVOICE_DUE_REMINDER = "invoice_due_reminder"
    INVOICE_OVERDUE = "invoice_overdue"
    PAYMENT_RECEIVED = "payment_received"
    PAYMENT_CONFIRMED = "payment_confirmed"
    CONTRACT_EXPIRING = "contract_expiring"
    CONTRACT_RENEWED = "contract_renewed"
    WELCOME = "welcome"


class NotificationChannel(str, Enum):
    """Notification delivery channels."""

    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"


class Notification(BaseModel):
    """Notification model."""

    id: Optional[UUID] = None
    tenant_id: UUID
    customer_id: UUID
    notification_type: NotificationType
    channel: NotificationChannel
    recipient: str  # Email or phone number
    subject: Optional[str] = None
    body: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    sent_at: Optional[date] = None
    delivered: bool = False
    error_message: Optional[str] = None


class NotificationService:
    """Service for sending notifications."""

    def __init__(
        self,
        customer_repo: CustomerRepository,
        invoice_repo: InvoiceRepository,
        contract_repo: ContractRepository,
        tenant_repo: TenantRepository,
    ):
        self.customer_repo = customer_repo
        self.invoice_repo = invoice_repo
        self.contract_repo = contract_repo
        self.tenant_repo = tenant_repo

    async def send_invoice_notification(
        self,
        tenant_id: UUID,
        invoice: Invoice,
        notification_type: NotificationType = NotificationType.INVOICE_CREATED,
    ) -> Optional[Notification]:
        """Send an invoice notification to the customer."""
        customer = await self.customer_repo.get_by_id(invoice.customer_id)
        if not customer:
            logger.error(f"Customer {invoice.customer_id} not found")
            return None

        if not customer.accepts_email_notifications:
            logger.info(f"Customer {customer.id} has email notifications disabled")
            return None

        tenant = await self.tenant_repo.get_by_id(tenant_id)
        if not tenant:
            logger.error(f"Tenant {tenant_id} not found")
            return None

        # Generate email content based on type
        subject, body = self._generate_invoice_email(
            notification_type, customer, invoice, tenant.name
        )

        notification = Notification(
            tenant_id=tenant_id,
            customer_id=customer.id,
            notification_type=notification_type,
            channel=NotificationChannel.EMAIL,
            recipient=customer.email,
            subject=subject,
            body=body,
            metadata={
                "invoice_id": str(invoice.id),
                "invoice_number": invoice.invoice_number,
                "amount": float(invoice.total),
            },
        )

        # In production, this would actually send the email
        # For now, we just log it
        logger.info(
            f"Sending {notification_type.value} email to {customer.email} "
            f"for invoice {invoice.invoice_number}"
        )

        # Simulate sending
        notification.sent_at = date.today()
        notification.delivered = True

        return notification

    def _generate_invoice_email(
        self,
        notification_type: NotificationType,
        customer: Customer,
        invoice: Invoice,
        business_name: str,
    ) -> tuple[str, str]:
        """Generate email subject and body for invoice notifications."""
        customer_name = customer.first_name

        if notification_type == NotificationType.INVOICE_CREATED:
            subject = f"Nueva factura {invoice.invoice_number} - {business_name}"
            body = f"""
Estimado/a {customer_name},

Se ha generado una nueva factura para su cuenta.

Detalles de la factura:
- Numero: {invoice.invoice_number}
- Fecha de emision: {invoice.issue_date.strftime('%d/%m/%Y')}
- Fecha de vencimiento: {invoice.due_date.strftime('%d/%m/%Y')}
- Monto total: ₡{invoice.total:,.2f}

Por favor realice su pago antes de la fecha de vencimiento para evitar cargos por mora.

Puede realizar su pago via SINPE Movil o transferencia bancaria.

Gracias por su preferencia.

Atentamente,
{business_name}
"""

        elif notification_type == NotificationType.INVOICE_DUE_REMINDER:
            days_until_due = (invoice.due_date - date.today()).days
            subject = f"Recordatorio: Factura {invoice.invoice_number} vence en {days_until_due} dias"
            body = f"""
Estimado/a {customer_name},

Le recordamos que su factura {invoice.invoice_number} vence el {invoice.due_date.strftime('%d/%m/%Y')}.

Monto pendiente: ₡{invoice.balance_due:,.2f}

Por favor realice su pago a tiempo para evitar cargos por mora.

Atentamente,
{business_name}
"""

        elif notification_type == NotificationType.INVOICE_OVERDUE:
            days_overdue = (date.today() - invoice.due_date).days
            subject = f"URGENTE: Factura {invoice.invoice_number} vencida"
            body = f"""
Estimado/a {customer_name},

Su factura {invoice.invoice_number} esta vencida desde hace {days_overdue} dias.

Monto pendiente: ₡{invoice.balance_due:,.2f}
{f'Cargo por mora aplicado: ₡{invoice.late_fee_amount:,.2f}' if invoice.late_fee_applied else ''}

Por favor regularice su situacion a la brevedad posible para evitar la suspension del servicio.

Atentamente,
{business_name}
"""

        else:
            subject = f"Notificacion - {business_name}"
            body = f"Estimado/a {customer_name}, tiene una notificacion pendiente."

        return subject, body

    async def send_payment_confirmation(
        self,
        tenant_id: UUID,
        payment: Payment,
        invoice: Optional[Invoice] = None,
    ) -> Optional[Notification]:
        """Send payment confirmation to customer."""
        customer = await self.customer_repo.get_by_id(payment.customer_id)
        if not customer:
            return None

        if not customer.accepts_email_notifications:
            return None

        tenant = await self.tenant_repo.get_by_id(tenant_id)
        if not tenant:
            return None

        subject = f"Pago recibido - {payment.payment_number}"
        body = f"""
Estimado/a {customer.first_name},

Hemos recibido su pago exitosamente.

Detalles del pago:
- Numero de pago: {payment.payment_number}
- Fecha: {payment.payment_date.strftime('%d/%m/%Y')}
- Monto: ₡{payment.amount:,.2f}
- Metodo: {payment.method.value.replace('_', ' ').title()}
{f'- Factura: {invoice.invoice_number}' if invoice else ''}

Gracias por su pago.

Atentamente,
{tenant.name}
"""

        notification = Notification(
            tenant_id=tenant_id,
            customer_id=customer.id,
            notification_type=NotificationType.PAYMENT_RECEIVED,
            channel=NotificationChannel.EMAIL,
            recipient=customer.email,
            subject=subject,
            body=body,
            metadata={
                "payment_id": str(payment.id),
                "payment_number": payment.payment_number,
                "amount": float(payment.amount),
            },
        )

        logger.info(f"Sending payment confirmation to {customer.email}")
        notification.sent_at = date.today()
        notification.delivered = True

        return notification

    async def send_contract_expiration_reminder(
        self,
        tenant_id: UUID,
        contract: Contract,
        days_until_expiration: int,
    ) -> Optional[Notification]:
        """Send contract expiration reminder."""
        customer = await self.customer_repo.get_by_id(contract.customer_id)
        if not customer:
            return None

        if not customer.accepts_email_notifications:
            return None

        tenant = await self.tenant_repo.get_by_id(tenant_id)
        if not tenant:
            return None

        subject = f"Su contrato vence en {days_until_expiration} dias"
        body = f"""
Estimado/a {customer.first_name},

Le informamos que su contrato de alquiler {contract.contract_number}
vence el {contract.end_date.strftime('%d/%m/%Y')}.

{'Su contrato se renovara automaticamente.' if contract.auto_renew else 'Por favor contactenos si desea renovar su contrato.'}

Condiciones actuales:
- Tarifa mensual: ₡{contract.effective_monthly_rate:,.2f}

Si tiene alguna pregunta o desea hacer cambios, no dude en contactarnos.

Atentamente,
{tenant.name}
"""

        notification = Notification(
            tenant_id=tenant_id,
            customer_id=customer.id,
            notification_type=NotificationType.CONTRACT_EXPIRING,
            channel=NotificationChannel.EMAIL,
            recipient=customer.email,
            subject=subject,
            body=body,
            metadata={
                "contract_id": str(contract.id),
                "contract_number": contract.contract_number,
                "expiration_date": contract.end_date.isoformat() if contract.end_date else None,
            },
        )

        logger.info(f"Sending contract expiration reminder to {customer.email}")
        notification.sent_at = date.today()
        notification.delivered = True

        return notification

    async def check_and_send_due_reminders(
        self,
        tenant_id: UUID,
        days_before_due: int = 5,
    ) -> List[Notification]:
        """Check for invoices due soon and send reminders."""
        notifications: List[Notification] = []
        target_date = date.today() + timedelta(days=days_before_due)

        invoices = await self.invoice_repo.list_by_tenant(
            tenant_id=tenant_id,
            skip=0,
            limit=10000,
        )

        for invoice in invoices:
            if invoice.status != InvoiceStatus.SENT:
                continue
            if invoice.balance_due <= 0:
                continue
            if invoice.due_date != target_date:
                continue

            notification = await self.send_invoice_notification(
                tenant_id=tenant_id,
                invoice=invoice,
                notification_type=NotificationType.INVOICE_DUE_REMINDER,
            )
            if notification:
                notifications.append(notification)

        return notifications

    async def check_and_send_overdue_notices(
        self,
        tenant_id: UUID,
    ) -> List[Notification]:
        """Check for overdue invoices and send notices."""
        notifications: List[Notification] = []

        invoices = await self.invoice_repo.list_by_tenant(
            tenant_id=tenant_id,
            skip=0,
            limit=10000,
        )

        for invoice in invoices:
            if invoice.status not in [InvoiceStatus.SENT, InvoiceStatus.OVERDUE]:
                continue
            if invoice.balance_due <= 0:
                continue
            if not invoice.is_overdue:
                continue

            # Only send once per week for overdue invoices
            days_overdue = (date.today() - invoice.due_date).days
            if days_overdue % 7 != 0:
                continue

            notification = await self.send_invoice_notification(
                tenant_id=tenant_id,
                invoice=invoice,
                notification_type=NotificationType.INVOICE_OVERDUE,
            )
            if notification:
                notifications.append(notification)

        return notifications

    async def check_and_send_contract_reminders(
        self,
        tenant_id: UUID,
    ) -> List[Notification]:
        """Check for expiring contracts and send reminders."""
        notifications: List[Notification] = []

        contracts = await self.contract_repo.list_by_tenant(
            tenant_id=tenant_id,
            skip=0,
            limit=10000,
        )

        for contract in contracts:
            if contract.status != ContractStatus.ACTIVE:
                continue
            if not contract.end_date:
                continue

            days_until_expiration = (contract.end_date - date.today()).days

            # Send reminders at 30, 15, and 7 days
            if days_until_expiration in [30, 15, 7]:
                notification = await self.send_contract_expiration_reminder(
                    tenant_id=tenant_id,
                    contract=contract,
                    days_until_expiration=days_until_expiration,
                )
                if notification:
                    notifications.append(notification)

        return notifications

    async def send_welcome_email(
        self,
        tenant_id: UUID,
        customer: Customer,
    ) -> Optional[Notification]:
        """Send welcome email to new customer."""
        if not customer.accepts_email_notifications:
            return None

        tenant = await self.tenant_repo.get_by_id(tenant_id)
        if not tenant:
            return None

        subject = f"Bienvenido/a a {tenant.name}"
        body = f"""
Estimado/a {customer.first_name},

¡Bienvenido/a a {tenant.name}!

Gracias por confiar en nosotros para sus necesidades de almacenamiento.

Si tiene alguna pregunta, no dude en contactarnos:
- Email: {tenant.email}
{f'- Telefono: {tenant.phone}' if tenant.phone else ''}

Atentamente,
El equipo de {tenant.name}
"""

        notification = Notification(
            tenant_id=tenant_id,
            customer_id=customer.id,
            notification_type=NotificationType.WELCOME,
            channel=NotificationChannel.EMAIL,
            recipient=customer.email,
            subject=subject,
            body=body,
        )

        logger.info(f"Sending welcome email to {customer.email}")
        notification.sent_at = date.today()
        notification.delivered = True

        return notification
