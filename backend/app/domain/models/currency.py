"""Currency and exchange rate models."""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.models.base import TenantScopedEntity


class SupportedCurrency(str, Enum):
    """Supported currencies for the platform."""

    CRC = "CRC"  # Costa Rican Colón (primary)
    USD = "USD"  # US Dollar
    EUR = "EUR"  # Euro


class ExchangeRateSource(str, Enum):
    """Source of exchange rate data."""

    BCCR = "bccr"  # Banco Central de Costa Rica
    MANUAL = "manual"  # Manually entered
    API = "api"  # Third-party API


class ExchangeRate(TenantScopedEntity):
    """Exchange rate record."""

    from_currency: str = Field(..., max_length=3, description="Source currency code")
    to_currency: str = Field(..., max_length=3, description="Target currency code")
    rate: Decimal = Field(..., gt=0, description="Exchange rate")
    rate_date: date = Field(default_factory=date.today, description="Date rate is valid for")
    source: ExchangeRateSource = Field(default=ExchangeRateSource.BCCR)
    is_buy_rate: bool = Field(default=True, description="True for buy rate, False for sell rate")


class ExchangeRateCreate(BaseModel):
    """Schema for creating an exchange rate."""

    from_currency: str = Field(..., max_length=3)
    to_currency: str = Field(..., max_length=3)
    rate: Decimal = Field(..., gt=0)
    rate_date: date = Field(default_factory=date.today)
    source: ExchangeRateSource = Field(default=ExchangeRateSource.MANUAL)
    is_buy_rate: bool = Field(default=True)


class CurrencyConfig(BaseModel):
    """Currency configuration for a tenant."""

    primary_currency: SupportedCurrency = Field(default=SupportedCurrency.CRC)
    accepted_currencies: list[SupportedCurrency] = Field(
        default_factory=lambda: [SupportedCurrency.CRC, SupportedCurrency.USD]
    )
    auto_convert_to_primary: bool = Field(
        default=True, description="Automatically convert foreign currency payments to primary"
    )
    display_dual_currency: bool = Field(
        default=True, description="Show amounts in both primary and USD"
    )


class CurrencyAmount(BaseModel):
    """Amount in a specific currency with optional conversion."""

    amount: Decimal = Field(..., description="Amount in original currency")
    currency: SupportedCurrency = Field(default=SupportedCurrency.CRC)
    converted_amount: Optional[Decimal] = Field(None, description="Amount converted to primary currency")
    converted_currency: Optional[SupportedCurrency] = Field(None)
    exchange_rate: Optional[Decimal] = Field(None, description="Rate used for conversion")
    exchange_rate_date: Optional[date] = Field(None)


# BCCR Exchange Rate Codes
# These are the indicator codes used by BCCR's public API
BCCR_INDICATORS = {
    "USD_BUY": "317",   # Tipo de cambio de compra del dólar
    "USD_SELL": "318",  # Tipo de cambio de venta del dólar
    "EUR_BUY": "333",   # Tipo de cambio de compra del euro
    "EUR_SELL": "334",  # Tipo de cambio de venta del euro
}


class BCCRExchangeRateResponse(BaseModel):
    """Response from BCCR exchange rate service."""

    indicator: str
    date: date
    value: Decimal
    currency: str
    description: str


class MultiCurrencyInvoiceSummary(BaseModel):
    """Invoice amounts in multiple currencies."""

    subtotal_original: Decimal
    tax_original: Decimal
    total_original: Decimal
    currency_original: SupportedCurrency

    subtotal_crc: Decimal
    tax_crc: Decimal
    total_crc: Decimal

    subtotal_usd: Optional[Decimal] = None
    total_usd: Optional[Decimal] = None

    exchange_rate_usd: Optional[Decimal] = None
    exchange_rate_date: Optional[date] = None
