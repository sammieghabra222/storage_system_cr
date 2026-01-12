"""Tax configuration models for Costa Rica IVA."""
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.models.base import TenantScopedEntity


class TarifaIVA(str, Enum):
    """Costa Rica IVA rate codes per Hacienda spec."""

    EXENTO = "01"  # Exempt (0%)
    TARIFA_REDUCIDA_1 = "02"  # Reduced rate 1% (canasta básica)
    TARIFA_REDUCIDA_2 = "03"  # Reduced rate 2%
    TARIFA_REDUCIDA_4 = "04"  # Reduced rate 4% (health services)
    TRANSITORIO_0 = "05"  # Transitory 0%
    TRANSITORIO_4 = "06"  # Transitory 4%
    TRANSITORIO_8 = "07"  # Transitory 8%
    TARIFA_GENERAL = "08"  # General rate 13%


# Mapping of IVA codes to actual rates
IVA_RATES: dict[TarifaIVA, Decimal] = {
    TarifaIVA.EXENTO: Decimal("0"),
    TarifaIVA.TARIFA_REDUCIDA_1: Decimal("1"),
    TarifaIVA.TARIFA_REDUCIDA_2: Decimal("2"),
    TarifaIVA.TARIFA_REDUCIDA_4: Decimal("4"),
    TarifaIVA.TRANSITORIO_0: Decimal("0"),
    TarifaIVA.TRANSITORIO_4: Decimal("4"),
    TarifaIVA.TRANSITORIO_8: Decimal("8"),
    TarifaIVA.TARIFA_GENERAL: Decimal("13"),
}


class TaxCategory(str, Enum):
    """Tax categories for services/products."""

    STORAGE_SERVICE = "storage_service"  # General storage service
    CLIMATE_CONTROLLED = "climate_controlled"  # Climate controlled storage
    VEHICLE_STORAGE = "vehicle_storage"  # Vehicle storage
    LATE_FEE = "late_fee"  # Late payment fee
    DEPOSIT = "deposit"  # Security deposit (typically exempt)
    OTHER_SERVICE = "other_service"  # Other services


# Default IVA rate for each category
DEFAULT_CATEGORY_RATES: dict[TaxCategory, TarifaIVA] = {
    TaxCategory.STORAGE_SERVICE: TarifaIVA.TARIFA_GENERAL,  # 13%
    TaxCategory.CLIMATE_CONTROLLED: TarifaIVA.TARIFA_GENERAL,  # 13%
    TaxCategory.VEHICLE_STORAGE: TarifaIVA.TARIFA_GENERAL,  # 13%
    TaxCategory.LATE_FEE: TarifaIVA.TARIFA_GENERAL,  # 13%
    TaxCategory.DEPOSIT: TarifaIVA.EXENTO,  # 0% - deposits are exempt
    TaxCategory.OTHER_SERVICE: TarifaIVA.TARIFA_GENERAL,  # 13%
}


class TaxExemptionReason(str, Enum):
    """Reasons for tax exemption."""

    NONPROFIT = "nonprofit"  # Non-profit organization
    GOVERNMENT = "government"  # Government entity
    EXPORT = "export"  # Export services
    FREE_ZONE = "free_zone"  # Free trade zone
    DIPLOMATIC = "diplomatic"  # Diplomatic exemption
    OTHER = "other"  # Other authorized exemption


class TaxConfig(TenantScopedEntity):
    """Tax configuration for a tenant."""

    default_iva_rate: TarifaIVA = Field(
        default=TarifaIVA.TARIFA_GENERAL,
        description="Default IVA rate for new invoices",
    )
    apply_iva_to_storage: bool = Field(
        default=True,
        description="Apply IVA to storage rental charges",
    )
    apply_iva_to_late_fees: bool = Field(
        default=True,
        description="Apply IVA to late payment fees",
    )
    apply_iva_to_deposits: bool = Field(
        default=False,
        description="Apply IVA to security deposits",
    )

    # Category-specific rate overrides
    storage_rate: Optional[TarifaIVA] = None
    climate_controlled_rate: Optional[TarifaIVA] = None
    vehicle_storage_rate: Optional[TarifaIVA] = None
    late_fee_rate: Optional[TarifaIVA] = None

    # Exemption settings
    is_exempt: bool = Field(
        default=False,
        description="Tenant is exempt from IVA",
    )
    exemption_reason: Optional[TaxExemptionReason] = None
    exemption_document: Optional[str] = Field(
        None,
        max_length=100,
        description="Document number authorizing exemption",
    )


class TaxConfigCreate(BaseModel):
    """Schema for creating tax configuration."""

    default_iva_rate: TarifaIVA = TarifaIVA.TARIFA_GENERAL
    apply_iva_to_storage: bool = True
    apply_iva_to_late_fees: bool = True
    apply_iva_to_deposits: bool = False
    storage_rate: Optional[TarifaIVA] = None
    climate_controlled_rate: Optional[TarifaIVA] = None
    vehicle_storage_rate: Optional[TarifaIVA] = None
    late_fee_rate: Optional[TarifaIVA] = None
    is_exempt: bool = False
    exemption_reason: Optional[TaxExemptionReason] = None
    exemption_document: Optional[str] = Field(None, max_length=100)


class TaxConfigUpdate(BaseModel):
    """Schema for updating tax configuration."""

    default_iva_rate: Optional[TarifaIVA] = None
    apply_iva_to_storage: Optional[bool] = None
    apply_iva_to_late_fees: Optional[bool] = None
    apply_iva_to_deposits: Optional[bool] = None
    storage_rate: Optional[TarifaIVA] = None
    climate_controlled_rate: Optional[TarifaIVA] = None
    vehicle_storage_rate: Optional[TarifaIVA] = None
    late_fee_rate: Optional[TarifaIVA] = None
    is_exempt: Optional[bool] = None
    exemption_reason: Optional[TaxExemptionReason] = None
    exemption_document: Optional[str] = Field(None, max_length=100)


class TaxCalculation(BaseModel):
    """Result of a tax calculation."""

    subtotal: Decimal = Field(..., description="Amount before tax")
    tax_rate: Decimal = Field(..., description="Tax rate percentage")
    tax_rate_code: TarifaIVA = Field(..., description="Hacienda IVA code")
    tax_amount: Decimal = Field(..., description="Calculated tax amount")
    total: Decimal = Field(..., description="Total including tax")
    is_exempt: bool = Field(default=False)
    exemption_reason: Optional[str] = None


class TaxSummary(BaseModel):
    """Summary of taxes for an invoice or period."""

    subtotal: Decimal = Field(default=Decimal("0"))
    total_exempt: Decimal = Field(default=Decimal("0"))
    total_taxable: Decimal = Field(default=Decimal("0"))

    # Breakdown by rate
    tax_at_1_percent: Decimal = Field(default=Decimal("0"))
    tax_at_2_percent: Decimal = Field(default=Decimal("0"))
    tax_at_4_percent: Decimal = Field(default=Decimal("0"))
    tax_at_8_percent: Decimal = Field(default=Decimal("0"))
    tax_at_13_percent: Decimal = Field(default=Decimal("0"))

    total_tax: Decimal = Field(default=Decimal("0"))
    grand_total: Decimal = Field(default=Decimal("0"))
