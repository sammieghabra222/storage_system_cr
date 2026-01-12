"""Analytics service for reporting and dashboard data."""
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional
from uuid import UUID
from collections import defaultdict
import logging

from app.domain.models.storage_unit import UnitStatus
from app.domain.models.contract import ContractStatus
from app.domain.models.invoice import InvoiceStatus
from app.domain.models.payment import PaymentStatus, PaymentMethod
from app.infrastructure.repositories.base import (
    StorageUnitRepository,
    ContractRepository,
    CustomerRepository,
    InvoiceRepository,
    PaymentRepository,
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for generating analytics and reports."""

    def __init__(
        self,
        unit_repo: StorageUnitRepository,
        contract_repo: ContractRepository,
        customer_repo: CustomerRepository,
        invoice_repo: InvoiceRepository,
        payment_repo: PaymentRepository,
    ):
        self.unit_repo = unit_repo
        self.contract_repo = contract_repo
        self.customer_repo = customer_repo
        self.invoice_repo = invoice_repo
        self.payment_repo = payment_repo

    async def get_dashboard_summary(self, tenant_id: UUID) -> Dict[str, Any]:
        """Get summary data for the main dashboard."""
        # Get all data
        units = await self.unit_repo.list_by_tenant(tenant_id, 0, 10000)
        contracts = await self.contract_repo.list_by_tenant(tenant_id, 0, 10000)
        customers = await self.customer_repo.list_by_tenant(tenant_id, 0, 10000)
        invoices = await self.invoice_repo.list_by_tenant(tenant_id, 0, 10000)
        payments = await self.payment_repo.list_by_tenant(tenant_id, 0, 10000)

        # Calculate unit statistics
        total_units = len(units)
        occupied_units = len([u for u in units if u.status == UnitStatus.OCCUPIED])
        available_units = len([u for u in units if u.status == UnitStatus.AVAILABLE])
        occupancy_rate = (occupied_units / total_units * 100) if total_units > 0 else 0

        # Calculate revenue statistics
        active_contracts = [c for c in contracts if c.status == ContractStatus.ACTIVE]
        monthly_revenue = sum(c.effective_monthly_rate for c in active_contracts)

        # Calculate payment statistics for current month
        today = date.today()
        month_start = today.replace(day=1)
        current_month_payments = [
            p for p in payments
            if p.status == PaymentStatus.CONFIRMED
            and p.payment_date >= month_start
        ]
        collected_this_month = sum(p.amount for p in current_month_payments)

        # Calculate outstanding
        outstanding_invoices = [
            inv for inv in invoices
            if inv.status in [InvoiceStatus.SENT, InvoiceStatus.OVERDUE, InvoiceStatus.PARTIAL]
            and inv.balance_due > 0
        ]
        total_outstanding = sum(inv.balance_due for inv in outstanding_invoices)

        # Calculate overdue
        overdue_invoices = [inv for inv in outstanding_invoices if inv.is_overdue]
        total_overdue = sum(inv.balance_due for inv in overdue_invoices)

        return {
            "units": {
                "total": total_units,
                "occupied": occupied_units,
                "available": available_units,
                "maintenance": len([u for u in units if u.status == UnitStatus.MAINTENANCE]),
                "occupancy_rate": round(occupancy_rate, 1),
            },
            "customers": {
                "total": len(customers),
                "active": len([c for c in customers if c.is_active]),
            },
            "contracts": {
                "total": len(contracts),
                "active": len(active_contracts),
                "expiring_soon": len([
                    c for c in active_contracts
                    if c.end_date and (c.end_date - today).days <= 30
                ]),
            },
            "revenue": {
                "monthly_expected": float(monthly_revenue),
                "collected_this_month": float(collected_this_month),
                "total_outstanding": float(total_outstanding),
                "total_overdue": float(total_overdue),
            },
            "invoices": {
                "pending_count": len([inv for inv in invoices if inv.status == InvoiceStatus.SENT]),
                "overdue_count": len(overdue_invoices),
            },
        }

    async def get_revenue_report(
        self,
        tenant_id: UUID,
        start_date: date,
        end_date: date,
        group_by: str = "month",
    ) -> Dict[str, Any]:
        """
        Get revenue report grouped by time period.

        Args:
            tenant_id: Tenant ID
            start_date: Report start date
            end_date: Report end date
            group_by: Grouping period ('day', 'week', 'month')
        """
        payments = await self.payment_repo.list_by_tenant(tenant_id, 0, 10000)
        invoices = await self.invoice_repo.list_by_tenant(tenant_id, 0, 10000)

        # Filter by date range
        period_payments = [
            p for p in payments
            if p.status == PaymentStatus.CONFIRMED
            and start_date <= p.payment_date <= end_date
        ]

        period_invoices = [
            inv for inv in invoices
            if start_date <= inv.issue_date <= end_date
        ]

        # Group payments by period
        revenue_by_period: Dict[str, Decimal] = defaultdict(Decimal)
        for payment in period_payments:
            period_key = self._get_period_key(payment.payment_date, group_by)
            revenue_by_period[period_key] += payment.amount

        # Group invoices by period
        invoiced_by_period: Dict[str, Decimal] = defaultdict(Decimal)
        for invoice in period_invoices:
            period_key = self._get_period_key(invoice.issue_date, group_by)
            invoiced_by_period[period_key] += invoice.total

        # Get all period keys in range
        all_periods = self._get_all_periods(start_date, end_date, group_by)

        # Build time series data
        time_series = []
        for period in all_periods:
            time_series.append({
                "period": period,
                "invoiced": float(invoiced_by_period.get(period, 0)),
                "collected": float(revenue_by_period.get(period, 0)),
            })

        # Calculate totals
        total_invoiced = sum(inv.total for inv in period_invoices)
        total_collected = sum(p.amount for p in period_payments)

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "group_by": group_by,
            "time_series": time_series,
            "totals": {
                "invoiced": float(total_invoiced),
                "collected": float(total_collected),
                "collection_rate": float(total_collected / total_invoiced * 100) if total_invoiced > 0 else 0,
            },
        }

    def _get_period_key(self, d: date, group_by: str) -> str:
        """Get the period key for a date."""
        if group_by == "day":
            return d.strftime("%Y-%m-%d")
        elif group_by == "week":
            # ISO week
            return d.strftime("%Y-W%W")
        else:  # month
            return d.strftime("%Y-%m")

    def _get_all_periods(self, start_date: date, end_date: date, group_by: str) -> List[str]:
        """Get all period keys in a date range."""
        periods = []
        current = start_date

        while current <= end_date:
            period_key = self._get_period_key(current, group_by)
            if period_key not in periods:
                periods.append(period_key)

            if group_by == "day":
                current += timedelta(days=1)
            elif group_by == "week":
                current += timedelta(weeks=1)
            else:  # month
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)

        return periods

    async def get_occupancy_report(
        self,
        tenant_id: UUID,
    ) -> Dict[str, Any]:
        """Get occupancy breakdown by unit type and building."""
        units = await self.unit_repo.list_by_tenant(tenant_id, 0, 10000)

        # By unit type
        by_type: Dict[str, Dict[str, int]] = defaultdict(lambda: {"total": 0, "occupied": 0})
        for unit in units:
            by_type[unit.unit_type.value]["total"] += 1
            if unit.status == UnitStatus.OCCUPIED:
                by_type[unit.unit_type.value]["occupied"] += 1

        type_breakdown = [
            {
                "type": unit_type,
                "total": stats["total"],
                "occupied": stats["occupied"],
                "available": stats["total"] - stats["occupied"],
                "occupancy_rate": round(stats["occupied"] / stats["total"] * 100, 1) if stats["total"] > 0 else 0,
            }
            for unit_type, stats in by_type.items()
        ]

        # By building
        by_building: Dict[str, Dict[str, int]] = defaultdict(lambda: {"total": 0, "occupied": 0})
        for unit in units:
            building = unit.building or "Sin edificio"
            by_building[building]["total"] += 1
            if unit.status == UnitStatus.OCCUPIED:
                by_building[building]["occupied"] += 1

        building_breakdown = [
            {
                "building": building,
                "total": stats["total"],
                "occupied": stats["occupied"],
                "available": stats["total"] - stats["occupied"],
                "occupancy_rate": round(stats["occupied"] / stats["total"] * 100, 1) if stats["total"] > 0 else 0,
            }
            for building, stats in by_building.items()
        ]

        # Overall
        total = len(units)
        occupied = len([u for u in units if u.status == UnitStatus.OCCUPIED])

        return {
            "overall": {
                "total_units": total,
                "occupied": occupied,
                "available": len([u for u in units if u.status == UnitStatus.AVAILABLE]),
                "maintenance": len([u for u in units if u.status == UnitStatus.MAINTENANCE]),
                "occupancy_rate": round(occupied / total * 100, 1) if total > 0 else 0,
            },
            "by_type": type_breakdown,
            "by_building": building_breakdown,
        }

    async def get_payment_report(
        self,
        tenant_id: UUID,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """Get payment breakdown by method."""
        payments = await self.payment_repo.list_by_tenant(tenant_id, 0, 10000)

        # Filter by date range and confirmed status
        period_payments = [
            p for p in payments
            if p.status == PaymentStatus.CONFIRMED
            and start_date <= p.payment_date <= end_date
        ]

        # By payment method
        by_method: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"count": 0, "amount": Decimal(0)})
        for payment in period_payments:
            by_method[payment.method.value]["count"] += 1
            by_method[payment.method.value]["amount"] += payment.amount

        method_breakdown = [
            {
                "method": method,
                "count": stats["count"],
                "amount": float(stats["amount"]),
                "percentage": round(stats["count"] / len(period_payments) * 100, 1) if period_payments else 0,
            }
            for method, stats in by_method.items()
        ]

        # Calculate totals
        total_amount = sum(p.amount for p in period_payments)

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_payments": len(period_payments),
            "total_amount": float(total_amount),
            "by_method": method_breakdown,
        }

    async def get_aging_report(
        self,
        tenant_id: UUID,
    ) -> Dict[str, Any]:
        """Get accounts receivable aging report."""
        invoices = await self.invoice_repo.list_by_tenant(tenant_id, 0, 10000)
        customers = await self.customer_repo.list_by_tenant(tenant_id, 0, 10000)
        customer_map = {c.id: c for c in customers}

        # Filter to outstanding invoices
        outstanding = [
            inv for inv in invoices
            if inv.status in [InvoiceStatus.SENT, InvoiceStatus.OVERDUE, InvoiceStatus.PARTIAL]
            and inv.balance_due > 0
        ]

        today = date.today()

        # Aging buckets
        buckets = {
            "current": {"count": 0, "amount": Decimal(0), "invoices": []},
            "1_30_days": {"count": 0, "amount": Decimal(0), "invoices": []},
            "31_60_days": {"count": 0, "amount": Decimal(0), "invoices": []},
            "61_90_days": {"count": 0, "amount": Decimal(0), "invoices": []},
            "over_90_days": {"count": 0, "amount": Decimal(0), "invoices": []},
        }

        for invoice in outstanding:
            days_outstanding = (today - invoice.due_date).days
            customer = customer_map.get(invoice.customer_id)
            customer_name = customer.display_name if customer else "Desconocido"

            invoice_data = {
                "invoice_number": invoice.invoice_number,
                "customer_name": customer_name,
                "due_date": invoice.due_date.isoformat(),
                "amount": float(invoice.balance_due),
                "days_outstanding": days_outstanding,
            }

            if days_outstanding <= 0:
                bucket = "current"
            elif days_outstanding <= 30:
                bucket = "1_30_days"
            elif days_outstanding <= 60:
                bucket = "31_60_days"
            elif days_outstanding <= 90:
                bucket = "61_90_days"
            else:
                bucket = "over_90_days"

            buckets[bucket]["count"] += 1
            buckets[bucket]["amount"] += invoice.balance_due
            buckets[bucket]["invoices"].append(invoice_data)

        # Format buckets for response
        aging_summary = []
        bucket_labels = {
            "current": "Vigente",
            "1_30_days": "1-30 dias",
            "31_60_days": "31-60 dias",
            "61_90_days": "61-90 dias",
            "over_90_days": "Mas de 90 dias",
        }

        for bucket_key, bucket_data in buckets.items():
            aging_summary.append({
                "bucket": bucket_labels[bucket_key],
                "count": bucket_data["count"],
                "amount": float(bucket_data["amount"]),
                "invoices": bucket_data["invoices"],
            })

        total_outstanding = sum(inv.balance_due for inv in outstanding)

        return {
            "as_of_date": today.isoformat(),
            "total_outstanding": float(total_outstanding),
            "total_invoices": len(outstanding),
            "aging_summary": aging_summary,
        }

    async def get_customer_report(
        self,
        tenant_id: UUID,
    ) -> Dict[str, Any]:
        """Get customer statistics and top customers by revenue."""
        customers = await self.customer_repo.list_by_tenant(tenant_id, 0, 10000)
        contracts = await self.contract_repo.list_by_tenant(tenant_id, 0, 10000)
        payments = await self.payment_repo.list_by_tenant(tenant_id, 0, 10000)

        # Calculate revenue per customer
        customer_revenue: Dict[UUID, Decimal] = defaultdict(Decimal)
        for payment in payments:
            if payment.status == PaymentStatus.CONFIRMED:
                customer_revenue[payment.customer_id] += payment.amount

        # Build customer stats
        customer_stats = []
        for customer in customers:
            active_contracts = [
                c for c in contracts
                if c.customer_id == customer.id and c.status == ContractStatus.ACTIVE
            ]
            total_revenue = customer_revenue.get(customer.id, Decimal(0))

            customer_stats.append({
                "id": str(customer.id),
                "name": customer.display_name,
                "type": customer.customer_type.value,
                "active_contracts": len(active_contracts),
                "total_revenue": float(total_revenue),
                "is_active": customer.is_active,
            })

        # Sort by revenue descending
        customer_stats.sort(key=lambda x: x["total_revenue"], reverse=True)

        # Summary
        total_customers = len(customers)
        active_customers = len([c for c in customers if c.is_active])
        individual_customers = len([c for c in customers if c.customer_type.value == "individual"])
        business_customers = len([c for c in customers if c.customer_type.value == "business"])

        return {
            "summary": {
                "total": total_customers,
                "active": active_customers,
                "inactive": total_customers - active_customers,
                "individual": individual_customers,
                "business": business_customers,
            },
            "top_customers": customer_stats[:10],  # Top 10
            "all_customers": customer_stats,
        }
