"""Analytics API endpoints for reporting and dashboards."""
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_current_user, get_analytics_service
from app.domain.models.user import User
from app.domain.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard")
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """Get summary data for the main dashboard."""
    return await analytics_service.get_dashboard_summary(current_user.tenant_id)


@router.get("/revenue")
async def get_revenue_report(
    start_date: Optional[date] = Query(None, description="Report start date"),
    end_date: Optional[date] = Query(None, description="Report end date"),
    group_by: str = Query("month", description="Grouping period: day, week, month"),
    current_user: User = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Get revenue report grouped by time period.

    Defaults to last 12 months if no dates specified.
    """
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - timedelta(days=365)

    return await analytics_service.get_revenue_report(
        tenant_id=current_user.tenant_id,
        start_date=start_date,
        end_date=end_date,
        group_by=group_by,
    )


@router.get("/occupancy")
async def get_occupancy_report(
    current_user: User = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """Get occupancy breakdown by unit type and building."""
    return await analytics_service.get_occupancy_report(current_user.tenant_id)


@router.get("/payments")
async def get_payment_report(
    start_date: Optional[date] = Query(None, description="Report start date"),
    end_date: Optional[date] = Query(None, description="Report end date"),
    current_user: User = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """Get payment breakdown by method."""
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date.replace(day=1)  # First of current month

    return await analytics_service.get_payment_report(
        tenant_id=current_user.tenant_id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/aging")
async def get_aging_report(
    current_user: User = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """Get accounts receivable aging report."""
    return await analytics_service.get_aging_report(current_user.tenant_id)


@router.get("/customers")
async def get_customer_report(
    current_user: User = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """Get customer statistics and top customers by revenue."""
    return await analytics_service.get_customer_report(current_user.tenant_id)
