"""Billing service for automated invoice generation and late fee calculations."""
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID
import logging

from app.domain.models.contract import Contract, ContractStatus, BillingCycle
from app.domain.models.invoice import Invoice, InvoiceCreate, InvoiceLineItem, InvoiceStatus
from app.infrastructure.repositories.base import (
    ContractRepository,
    InvoiceRepository,
    CustomerRepository,
)

logger = logging.getLogger(__name__)

# Costa Rica IVA rate
IVA_RATE = Decimal("13.00")


class BillingService:
    """Service for billing operations."""

    def __init__(
        self,
        contract_repo: ContractRepository,
        invoice_repo: InvoiceRepository,
        customer_repo: CustomerRepository,
    ):
        self.contract_repo = contract_repo
        self.invoice_repo = invoice_repo
        self.customer_repo = customer_repo

    async def generate_recurring_invoices(
        self,
        tenant_id: UUID,
        billing_date: Optional[date] = None,
    ) -> List[Invoice]:
        """
        Generate invoices for all active contracts due on billing_date.

        Args:
            tenant_id: The tenant to generate invoices for
            billing_date: The date to check for billing (defaults to today)

        Returns:
            List of generated invoices
        """
        if billing_date is None:
            billing_date = date.today()

        generated_invoices: List[Invoice] = []

        # Get all active contracts for the tenant
        contracts = await self.contract_repo.list_by_tenant(
            tenant_id=tenant_id,
            skip=0,
            limit=10000,
        )

        active_contracts = [c for c in contracts if c.status == ContractStatus.ACTIVE]

        for contract in active_contracts:
            # Check if billing is due for this contract
            if self._is_billing_due(contract, billing_date):
                # Check if invoice already exists for this period
                existing = await self._check_existing_invoice(
                    tenant_id, contract, billing_date
                )
                if existing:
                    logger.info(f"Invoice already exists for contract {contract.id}")
                    continue

                # Generate the invoice
                invoice = await self._generate_invoice_for_contract(
                    tenant_id, contract, billing_date
                )
                if invoice:
                    generated_invoices.append(invoice)
                    logger.info(f"Generated invoice {invoice.invoice_number} for contract {contract.id}")

        return generated_invoices

    def _is_billing_due(self, contract: Contract, check_date: date) -> bool:
        """Check if billing is due for a contract on the given date."""
        # Check if contract is within its active period
        if contract.start_date > check_date:
            return False
        if contract.end_date and contract.end_date < check_date:
            return False

        # Check billing day
        if contract.billing_day == check_date.day:
            return True

        # Handle months with fewer days
        if check_date.day == self._last_day_of_month(check_date):
            if contract.billing_day > check_date.day:
                return True

        return False

    def _last_day_of_month(self, d: date) -> int:
        """Get the last day of the month for a given date."""
        next_month = d.replace(day=28) + timedelta(days=4)
        return (next_month - timedelta(days=next_month.day)).day

    async def _check_existing_invoice(
        self,
        tenant_id: UUID,
        contract: Contract,
        billing_date: date,
    ) -> bool:
        """Check if an invoice already exists for this billing period."""
        # Calculate the billing period
        period_start, period_end = self._calculate_billing_period(
            contract, billing_date
        )

        # Get existing invoices for this contract
        invoices = await self.invoice_repo.list_by_tenant(
            tenant_id=tenant_id,
            skip=0,
            limit=1000,
        )

        for invoice in invoices:
            if (
                invoice.contract_id == contract.id
                and invoice.period_start == period_start
                and invoice.period_end == period_end
                and invoice.status != InvoiceStatus.CANCELLED
            ):
                return True

        return False

    def _calculate_billing_period(
        self,
        contract: Contract,
        billing_date: date,
    ) -> Tuple[date, date]:
        """Calculate the billing period based on billing cycle."""
        if contract.billing_cycle == BillingCycle.MONTHLY:
            # Period is the current month
            period_start = billing_date.replace(day=1)
            next_month = period_start + timedelta(days=32)
            period_end = next_month.replace(day=1) - timedelta(days=1)
        elif contract.billing_cycle == BillingCycle.QUARTERLY:
            # Period is 3 months
            period_start = billing_date.replace(day=1)
            period_end = (period_start + timedelta(days=92)).replace(day=1) - timedelta(days=1)
        elif contract.billing_cycle == BillingCycle.SEMI_ANNUAL:
            # Period is 6 months
            period_start = billing_date.replace(day=1)
            period_end = (period_start + timedelta(days=183)).replace(day=1) - timedelta(days=1)
        else:  # ANNUAL
            # Period is 12 months
            period_start = billing_date.replace(day=1)
            period_end = period_start.replace(year=period_start.year + 1) - timedelta(days=1)

        return period_start, period_end

    async def _generate_invoice_for_contract(
        self,
        tenant_id: UUID,
        contract: Contract,
        billing_date: date,
    ) -> Optional[Invoice]:
        """Generate an invoice for a contract."""
        try:
            # Get customer info
            customer = await self.customer_repo.get_by_id(contract.customer_id)
            if not customer:
                logger.error(f"Customer {contract.customer_id} not found for contract {contract.id}")
                return None

            # Calculate billing period
            period_start, period_end = self._calculate_billing_period(contract, billing_date)

            # Calculate amount based on billing cycle
            amount = self._calculate_billing_amount(contract)

            # Create line items
            line_items = [
                InvoiceLineItem(
                    description=f"Alquiler de bodega - {period_start.strftime('%B %Y')}",
                    quantity=Decimal("1"),
                    unit_price=amount,
                    tax_rate=IVA_RATE,
                    discount_percent=contract.discount_percent or Decimal("0"),
                )
            ]

            # Calculate due date (billing date + grace period)
            due_date = billing_date + timedelta(days=contract.grace_period_days)

            # Generate invoice number
            invoice_number = await self._generate_invoice_number(tenant_id)

            # Create invoice
            invoice_data = InvoiceCreate(
                customer_id=contract.customer_id,
                contract_id=contract.id,
                invoice_number=invoice_number,
                issue_date=billing_date,
                due_date=due_date,
                period_start=period_start,
                period_end=period_end,
                line_items=line_items,
                currency="CRC",
            )

            # Calculate totals
            subtotal = sum(item.subtotal for item in line_items)
            tax_total = sum(item.tax_amount for item in line_items)
            total = subtotal + tax_total

            invoice = Invoice(
                tenant_id=tenant_id,
                customer_id=invoice_data.customer_id,
                contract_id=invoice_data.contract_id,
                invoice_number=invoice_number,
                status=InvoiceStatus.DRAFT,
                issue_date=invoice_data.issue_date,
                due_date=invoice_data.due_date,
                period_start=invoice_data.period_start,
                period_end=invoice_data.period_end,
                line_items=invoice_data.line_items,
                subtotal=subtotal,
                tax_total=tax_total,
                discount_total=Decimal("0"),
                total=total,
                currency=invoice_data.currency,
            )

            created_invoice = await self.invoice_repo.create_for_tenant(
                tenant_id=tenant_id,
                entity=invoice,
            )

            return created_invoice

        except Exception as e:
            logger.error(f"Error generating invoice for contract {contract.id}: {e}")
            return None

    def _calculate_billing_amount(self, contract: Contract) -> Decimal:
        """Calculate the billing amount based on billing cycle."""
        monthly_rate = contract.effective_monthly_rate

        if contract.billing_cycle == BillingCycle.MONTHLY:
            return monthly_rate
        elif contract.billing_cycle == BillingCycle.QUARTERLY:
            return monthly_rate * 3
        elif contract.billing_cycle == BillingCycle.SEMI_ANNUAL:
            return monthly_rate * 6
        else:  # ANNUAL
            return monthly_rate * 12

    async def _generate_invoice_number(self, tenant_id: UUID) -> str:
        """Generate a unique invoice number."""
        # Get count of existing invoices for numbering
        invoices = await self.invoice_repo.list_by_tenant(
            tenant_id=tenant_id,
            skip=0,
            limit=1,
        )
        # Simple sequential numbering - in production would use a sequence
        count = len(invoices) + 1
        year = date.today().year
        return f"FAC-{year}-{count:05d}"

    async def apply_late_fees(
        self,
        tenant_id: UUID,
        check_date: Optional[date] = None,
    ) -> List[Invoice]:
        """
        Apply late fees to overdue invoices.

        Args:
            tenant_id: The tenant to check
            check_date: Date to check for overdue (defaults to today)

        Returns:
            List of invoices that had late fees applied
        """
        if check_date is None:
            check_date = date.today()

        updated_invoices: List[Invoice] = []

        # Get all sent invoices
        invoices = await self.invoice_repo.list_by_tenant(
            tenant_id=tenant_id,
            skip=0,
            limit=10000,
        )

        for invoice in invoices:
            # Skip if not eligible for late fee
            if invoice.status not in [InvoiceStatus.SENT, InvoiceStatus.OVERDUE, InvoiceStatus.PARTIAL]:
                continue
            if invoice.late_fee_applied:
                continue
            if invoice.balance_due <= 0:
                continue

            # Check if past due date + grace period
            if not invoice.contract_id:
                continue

            contract = await self.contract_repo.get_by_id(invoice.contract_id)
            if not contract:
                continue

            grace_end_date = invoice.due_date + timedelta(days=contract.grace_period_days)

            if check_date > grace_end_date:
                # Calculate late fee
                late_fee = self._calculate_late_fee(invoice, contract)

                if late_fee > 0:
                    # Update invoice
                    invoice.late_fee_applied = True
                    invoice.late_fee_amount = late_fee
                    invoice.status = InvoiceStatus.OVERDUE

                    updated = await self.invoice_repo.update(invoice.id, invoice)
                    if updated:
                        updated_invoices.append(updated)
                        logger.info(
                            f"Applied late fee of {late_fee} to invoice {invoice.invoice_number}"
                        )

        return updated_invoices

    def _calculate_late_fee(self, invoice: Invoice, contract: Contract) -> Decimal:
        """Calculate the late fee for an invoice."""
        # Use percentage if set, otherwise flat amount
        if contract.late_fee_percent:
            return invoice.balance_due * (contract.late_fee_percent / 100)
        return contract.late_fee_amount

    async def get_billing_summary(
        self,
        tenant_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict:
        """
        Get a billing summary for the tenant.

        Args:
            tenant_id: The tenant ID
            start_date: Start of period (defaults to first of current month)
            end_date: End of period (defaults to today)

        Returns:
            Dictionary with billing statistics
        """
        if start_date is None:
            start_date = date.today().replace(day=1)
        if end_date is None:
            end_date = date.today()

        invoices = await self.invoice_repo.list_by_tenant(
            tenant_id=tenant_id,
            skip=0,
            limit=10000,
        )

        # Filter by date range
        period_invoices = [
            inv for inv in invoices
            if start_date <= inv.issue_date <= end_date
        ]

        # Calculate totals
        total_invoiced = sum(inv.total for inv in period_invoices)
        total_collected = sum(inv.amount_paid for inv in period_invoices)
        total_outstanding = sum(inv.balance_due for inv in period_invoices if inv.balance_due > 0)
        overdue_invoices = [inv for inv in period_invoices if inv.is_overdue]
        total_overdue = sum(inv.balance_due for inv in overdue_invoices)
        late_fees_collected = sum(
            inv.late_fee_amount for inv in period_invoices
            if inv.late_fee_applied and inv.amount_paid >= inv.total
        )

        return {
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "total_invoices": len(period_invoices),
            "total_invoiced": float(total_invoiced),
            "total_collected": float(total_collected),
            "total_outstanding": float(total_outstanding),
            "overdue_count": len(overdue_invoices),
            "total_overdue": float(total_overdue),
            "late_fees_collected": float(late_fees_collected),
            "collection_rate": float(total_collected / total_invoiced * 100) if total_invoiced > 0 else 0,
        }

    async def calculate_prorated_amount(
        self,
        contract: Contract,
        start_date: date,
        end_date: date,
    ) -> Decimal:
        """
        Calculate prorated amount for partial month billing.

        Args:
            contract: The contract
            start_date: Start of the period to prorate
            end_date: End of the period to prorate

        Returns:
            Prorated amount
        """
        # Get the number of days in the month
        days_in_month = self._last_day_of_month(start_date)

        # Calculate days to bill
        days_to_bill = (end_date - start_date).days + 1

        # Calculate daily rate
        daily_rate = contract.effective_monthly_rate / days_in_month

        return daily_rate * days_to_bill
