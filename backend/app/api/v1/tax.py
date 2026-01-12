"""Tax configuration API endpoints."""
from decimal import Decimal
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query

from app.core.security import get_current_user
from app.domain.models import User, TarifaIVA, TaxCategory
from app.domain.services.tax_service import TaxService

router = APIRouter(prefix="/tax", tags=["Tax"])


def get_tax_service() -> TaxService:
    """Get tax service instance."""
    return TaxService()


@router.get("/rates", response_model=List[Dict[str, Any]])
async def get_iva_rates(
    current_user: User = Depends(get_current_user),
    service: TaxService = Depends(get_tax_service),
):
    """
    Get list of available IVA rates.

    Returns all Costa Rica IVA rate codes with their percentages.
    """
    return service.get_available_rates()


@router.get("/rate/{tarifa_code}", response_model=Dict[str, Any])
async def get_rate_info(
    tarifa_code: str,
    current_user: User = Depends(get_current_user),
    service: TaxService = Depends(get_tax_service),
):
    """Get information about a specific IVA rate code."""
    try:
        tarifa = TarifaIVA(tarifa_code)
        rate = service.get_iva_rate(tarifa)
        return {
            "code": tarifa.value,
            "rate": float(rate),
            "description": _get_rate_description(tarifa),
        }
    except ValueError:
        return {"error": "Invalid tarifa code", "valid_codes": [t.value for t in TarifaIVA]}


@router.post("/calculate", response_model=Dict[str, Any])
async def calculate_tax(
    amount: Decimal = Query(..., gt=0, description="Amount to calculate tax on"),
    tarifa_code: str = Query("08", description="IVA rate code (default: 13%)"),
    is_exempt: bool = Query(False, description="Whether the transaction is exempt"),
    current_user: User = Depends(get_current_user),
    service: TaxService = Depends(get_tax_service),
):
    """
    Calculate IVA for an amount.

    Returns subtotal, tax amount, and total.
    """
    try:
        tarifa = TarifaIVA(tarifa_code)
    except ValueError:
        tarifa = TarifaIVA.TARIFA_GENERAL

    calculation = service.calculate_tax(amount, tarifa, is_exempt)

    return {
        "subtotal": float(calculation.subtotal),
        "tax_rate": float(calculation.tax_rate),
        "tax_rate_code": calculation.tax_rate_code.value,
        "tax_amount": float(calculation.tax_amount),
        "total": float(calculation.total),
        "is_exempt": calculation.is_exempt,
    }


@router.post("/calculate-inclusive", response_model=Dict[str, Any])
async def calculate_tax_inclusive(
    total_amount: Decimal = Query(..., gt=0, description="Total amount including tax"),
    tarifa_code: str = Query("08", description="IVA rate code (default: 13%)"),
    current_user: User = Depends(get_current_user),
    service: TaxService = Depends(get_tax_service),
):
    """
    Calculate IVA breakdown from a tax-inclusive amount.

    Useful for reverse-calculating tax from prices that already include IVA.
    """
    try:
        tarifa = TarifaIVA(tarifa_code)
    except ValueError:
        tarifa = TarifaIVA.TARIFA_GENERAL

    calculation = service.calculate_inclusive_tax(total_amount, tarifa)

    return {
        "original_total": float(total_amount),
        "subtotal": float(calculation.subtotal),
        "tax_rate": float(calculation.tax_rate),
        "tax_rate_code": calculation.tax_rate_code.value,
        "tax_amount": float(calculation.tax_amount),
        "verified_total": float(calculation.total),
    }


@router.get("/categories", response_model=List[Dict[str, Any]])
async def get_tax_categories(
    current_user: User = Depends(get_current_user),
):
    """Get list of tax categories with their default rates."""
    from app.domain.models.tax import DEFAULT_CATEGORY_RATES

    return [
        {
            "category": cat.value,
            "default_rate_code": rate.value,
            "description": _get_category_description(cat),
            "description_es": _get_category_description_es(cat),
        }
        for cat, rate in DEFAULT_CATEGORY_RATES.items()
    ]


@router.get("/category/{category}", response_model=Dict[str, Any])
async def get_rate_for_category(
    category: str,
    current_user: User = Depends(get_current_user),
    service: TaxService = Depends(get_tax_service),
):
    """Get the IVA rate for a specific category."""
    try:
        tax_category = TaxCategory(category)
    except ValueError:
        return {
            "error": "Invalid category",
            "valid_categories": [c.value for c in TaxCategory],
        }

    tarifa, rate = await service.get_rate_for_category(
        current_user.tenant_id, tax_category
    )

    return {
        "category": category,
        "rate_code": tarifa.value,
        "rate": float(rate),
        "description": _get_category_description(tax_category),
    }


def _get_rate_description(tarifa: TarifaIVA) -> str:
    """Get English description for IVA rate."""
    descriptions = {
        TarifaIVA.EXENTO: "Exempt (0%)",
        TarifaIVA.TARIFA_REDUCIDA_1: "Reduced Rate 1% (basic goods)",
        TarifaIVA.TARIFA_REDUCIDA_2: "Reduced Rate 2%",
        TarifaIVA.TARIFA_REDUCIDA_4: "Reduced Rate 4% (health services)",
        TarifaIVA.TRANSITORIO_0: "Transitory 0%",
        TarifaIVA.TRANSITORIO_4: "Transitory 4%",
        TarifaIVA.TRANSITORIO_8: "Transitory 8%",
        TarifaIVA.TARIFA_GENERAL: "General Rate 13%",
    }
    return descriptions.get(tarifa, "Unknown")


def _get_category_description(category: TaxCategory) -> str:
    """Get English description for tax category."""
    descriptions = {
        TaxCategory.STORAGE_SERVICE: "Standard storage rental service",
        TaxCategory.CLIMATE_CONTROLLED: "Climate-controlled storage service",
        TaxCategory.VEHICLE_STORAGE: "Vehicle storage service",
        TaxCategory.LATE_FEE: "Late payment fee",
        TaxCategory.DEPOSIT: "Security deposit",
        TaxCategory.OTHER_SERVICE: "Other services",
    }
    return descriptions.get(category, "Unknown")


def _get_category_description_es(category: TaxCategory) -> str:
    """Get Spanish description for tax category."""
    descriptions = {
        TaxCategory.STORAGE_SERVICE: "Servicio de alquiler de bodega estándar",
        TaxCategory.CLIMATE_CONTROLLED: "Servicio de bodega con clima controlado",
        TaxCategory.VEHICLE_STORAGE: "Servicio de almacenamiento de vehículos",
        TaxCategory.LATE_FEE: "Cargo por mora",
        TaxCategory.DEPOSIT: "Depósito de garantía",
        TaxCategory.OTHER_SERVICE: "Otros servicios",
    }
    return descriptions.get(category, "Desconocido")
