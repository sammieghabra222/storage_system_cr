"""Tax calculation service for Costa Rica IVA."""
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional
from uuid import UUID

from app.domain.models.tax import (
    DEFAULT_CATEGORY_RATES,
    IVA_RATES,
    TarifaIVA,
    TaxCalculation,
    TaxCategory,
    TaxConfig,
    TaxSummary,
)


class TaxService:
    """Service for calculating Costa Rica IVA taxes."""

    # Costa Rica standard IVA rate
    STANDARD_IVA_RATE = Decimal("13")

    def __init__(self, tax_config_repository=None):
        self.tax_config_repo = tax_config_repository
        self._config_cache: dict[UUID, TaxConfig] = {}

    async def get_tenant_config(self, tenant_id: UUID) -> Optional[TaxConfig]:
        """Get tax configuration for a tenant."""
        if tenant_id in self._config_cache:
            return self._config_cache[tenant_id]

        if self.tax_config_repo:
            configs = await self.tax_config_repo.find_by(tenant_id=tenant_id)
            if configs:
                config = configs[0]
                self._config_cache[tenant_id] = config
                return config

        return None

    def get_iva_rate(self, tarifa: TarifaIVA) -> Decimal:
        """Get the percentage rate for an IVA code."""
        return IVA_RATES.get(tarifa, self.STANDARD_IVA_RATE)

    def get_tarifa_for_rate(self, rate: Decimal) -> TarifaIVA:
        """Get the IVA tarifa code for a given rate."""
        for tarifa, tarifa_rate in IVA_RATES.items():
            if tarifa_rate == rate:
                return tarifa
        return TarifaIVA.TARIFA_GENERAL

    async def get_rate_for_category(
        self,
        tenant_id: UUID,
        category: TaxCategory,
    ) -> tuple[TarifaIVA, Decimal]:
        """
        Get the IVA rate for a specific category.

        Returns tuple of (tarifa_code, rate_percentage)
        """
        config = await self.get_tenant_config(tenant_id)

        if config:
            # Check if tenant is exempt
            if config.is_exempt:
                return TarifaIVA.EXENTO, Decimal("0")

            # Check for category-specific overrides
            if category == TaxCategory.STORAGE_SERVICE and config.storage_rate:
                return config.storage_rate, self.get_iva_rate(config.storage_rate)

            if category == TaxCategory.CLIMATE_CONTROLLED and config.climate_controlled_rate:
                return config.climate_controlled_rate, self.get_iva_rate(config.climate_controlled_rate)

            if category == TaxCategory.VEHICLE_STORAGE and config.vehicle_storage_rate:
                return config.vehicle_storage_rate, self.get_iva_rate(config.vehicle_storage_rate)

            if category == TaxCategory.LATE_FEE:
                if not config.apply_iva_to_late_fees:
                    return TarifaIVA.EXENTO, Decimal("0")
                if config.late_fee_rate:
                    return config.late_fee_rate, self.get_iva_rate(config.late_fee_rate)

            if category == TaxCategory.DEPOSIT:
                if not config.apply_iva_to_deposits:
                    return TarifaIVA.EXENTO, Decimal("0")

        # Fall back to default rates
        default_tarifa = DEFAULT_CATEGORY_RATES.get(category, TarifaIVA.TARIFA_GENERAL)
        return default_tarifa, self.get_iva_rate(default_tarifa)

    def calculate_tax(
        self,
        amount: Decimal,
        tarifa: TarifaIVA,
        is_exempt: bool = False,
        exemption_reason: Optional[str] = None,
    ) -> TaxCalculation:
        """
        Calculate tax for an amount.

        Args:
            amount: The pre-tax amount
            tarifa: The IVA rate code
            is_exempt: Whether the transaction is exempt
            exemption_reason: Reason for exemption if applicable

        Returns:
            TaxCalculation with all amounts
        """
        if is_exempt:
            return TaxCalculation(
                subtotal=amount,
                tax_rate=Decimal("0"),
                tax_rate_code=TarifaIVA.EXENTO,
                tax_amount=Decimal("0"),
                total=amount,
                is_exempt=True,
                exemption_reason=exemption_reason,
            )

        rate = self.get_iva_rate(tarifa)
        tax_amount = (amount * rate / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        total = amount + tax_amount

        return TaxCalculation(
            subtotal=amount,
            tax_rate=rate,
            tax_rate_code=tarifa,
            tax_amount=tax_amount,
            total=total,
            is_exempt=False,
        )

    async def calculate_tax_for_category(
        self,
        tenant_id: UUID,
        amount: Decimal,
        category: TaxCategory,
    ) -> TaxCalculation:
        """
        Calculate tax for a specific category.

        Automatically determines the correct rate based on tenant config.
        """
        tarifa, rate = await self.get_rate_for_category(tenant_id, category)

        config = await self.get_tenant_config(tenant_id)
        is_exempt = config.is_exempt if config else False
        exemption_reason = None
        if is_exempt and config and config.exemption_reason:
            exemption_reason = config.exemption_reason.value

        return self.calculate_tax(amount, tarifa, is_exempt, exemption_reason)

    def calculate_summary(
        self,
        calculations: List[TaxCalculation],
    ) -> TaxSummary:
        """
        Calculate a summary from multiple tax calculations.

        Aggregates amounts by rate for Hacienda reporting.
        """
        summary = TaxSummary()

        for calc in calculations:
            summary.subtotal += calc.subtotal
            summary.grand_total += calc.total

            if calc.is_exempt or calc.tax_rate == Decimal("0"):
                summary.total_exempt += calc.subtotal
            else:
                summary.total_taxable += calc.subtotal
                summary.total_tax += calc.tax_amount

                # Categorize by rate
                if calc.tax_rate == Decimal("1"):
                    summary.tax_at_1_percent += calc.tax_amount
                elif calc.tax_rate == Decimal("2"):
                    summary.tax_at_2_percent += calc.tax_amount
                elif calc.tax_rate == Decimal("4"):
                    summary.tax_at_4_percent += calc.tax_amount
                elif calc.tax_rate == Decimal("8"):
                    summary.tax_at_8_percent += calc.tax_amount
                elif calc.tax_rate == Decimal("13"):
                    summary.tax_at_13_percent += calc.tax_amount

        return summary

    def calculate_inclusive_tax(
        self,
        total_amount: Decimal,
        tarifa: TarifaIVA,
    ) -> TaxCalculation:
        """
        Calculate tax when amount includes tax (reverse calculation).

        Useful for displaying tax breakdown on prices that already include IVA.
        """
        rate = self.get_iva_rate(tarifa)

        if rate == Decimal("0"):
            return TaxCalculation(
                subtotal=total_amount,
                tax_rate=Decimal("0"),
                tax_rate_code=tarifa,
                tax_amount=Decimal("0"),
                total=total_amount,
                is_exempt=True,
            )

        # Calculate base amount: base = total / (1 + rate/100)
        divisor = Decimal("1") + (rate / Decimal("100"))
        subtotal = (total_amount / divisor).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        tax_amount = total_amount - subtotal

        return TaxCalculation(
            subtotal=subtotal,
            tax_rate=rate,
            tax_rate_code=tarifa,
            tax_amount=tax_amount,
            total=total_amount,
            is_exempt=False,
        )

    def format_iva_breakdown(
        self,
        calculation: TaxCalculation,
        locale: str = "es",
    ) -> dict:
        """
        Format tax calculation for display.

        Returns a dictionary suitable for invoice display.
        """
        if locale == "es":
            return {
                "subtotal_label": "Subtotal",
                "subtotal": str(calculation.subtotal),
                "tax_label": f"IVA ({calculation.tax_rate}%)",
                "tax_amount": str(calculation.tax_amount),
                "total_label": "Total",
                "total": str(calculation.total),
                "is_exempt": calculation.is_exempt,
                "exempt_label": "Exento de IVA" if calculation.is_exempt else None,
            }
        else:
            return {
                "subtotal_label": "Subtotal",
                "subtotal": str(calculation.subtotal),
                "tax_label": f"IVA ({calculation.tax_rate}%)",
                "tax_amount": str(calculation.tax_amount),
                "total_label": "Total",
                "total": str(calculation.total),
                "is_exempt": calculation.is_exempt,
                "exempt_label": "Tax Exempt" if calculation.is_exempt else None,
            }

    @staticmethod
    def get_available_rates() -> list[dict]:
        """Get list of available IVA rates for configuration."""
        return [
            {"code": TarifaIVA.TARIFA_GENERAL.value, "rate": 13, "name": "General (13%)", "name_es": "General (13%)"},
            {"code": TarifaIVA.TARIFA_REDUCIDA_4.value, "rate": 4, "name": "Reduced 4%", "name_es": "Reducida 4%"},
            {"code": TarifaIVA.TARIFA_REDUCIDA_2.value, "rate": 2, "name": "Reduced 2%", "name_es": "Reducida 2%"},
            {"code": TarifaIVA.TARIFA_REDUCIDA_1.value, "rate": 1, "name": "Reduced 1%", "name_es": "Reducida 1%"},
            {"code": TarifaIVA.EXENTO.value, "rate": 0, "name": "Exempt (0%)", "name_es": "Exento (0%)"},
            {"code": TarifaIVA.TRANSITORIO_8.value, "rate": 8, "name": "Transitory 8%", "name_es": "Transitorio 8%"},
            {"code": TarifaIVA.TRANSITORIO_4.value, "rate": 4, "name": "Transitory 4%", "name_es": "Transitorio 4%"},
            {"code": TarifaIVA.TRANSITORIO_0.value, "rate": 0, "name": "Transitory 0%", "name_es": "Transitorio 0%"},
        ]
