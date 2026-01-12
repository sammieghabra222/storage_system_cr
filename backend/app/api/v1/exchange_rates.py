"""Exchange rates API endpoints."""
from datetime import date
from decimal import Decimal
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query

from app.core.security import get_current_user
from app.domain.models import User, SupportedCurrency
from app.domain.services.exchange_rate_service import ExchangeRateService

router = APIRouter(prefix="/exchange-rates", tags=["Exchange Rates"])


def get_exchange_rate_service() -> ExchangeRateService:
    """Get exchange rate service instance."""
    return ExchangeRateService()


@router.get("/current", response_model=Dict[str, Any])
async def get_current_rates(
    current_user: User = Depends(get_current_user),
    service: ExchangeRateService = Depends(get_exchange_rate_service),
):
    """
    Get current exchange rates from BCCR.

    Returns USD and EUR buy/sell rates relative to CRC.
    """
    rates = await service.get_all_rates()

    return {
        "date": date.today().isoformat(),
        "base_currency": "CRC",
        "rates": rates,
        "source": "BCCR",
    }


@router.get("/usd", response_model=Dict[str, Any])
async def get_usd_rate(
    rate_date: Optional[date] = Query(None, description="Date for historical rate"),
    rate_type: str = Query("buy", enum=["buy", "sell"], description="Buy or sell rate"),
    current_user: User = Depends(get_current_user),
    service: ExchangeRateService = Depends(get_exchange_rate_service),
):
    """Get USD to CRC exchange rate."""
    use_buy = rate_type == "buy"
    rate = await service.get_usd_rate(rate_date, use_buy_rate=use_buy)

    return {
        "currency": "USD",
        "base_currency": "CRC",
        "rate": float(rate) if rate else None,
        "rate_type": rate_type,
        "date": (rate_date or date.today()).isoformat(),
        "source": "BCCR",
    }


@router.get("/eur", response_model=Dict[str, Any])
async def get_eur_rate(
    rate_date: Optional[date] = Query(None, description="Date for historical rate"),
    rate_type: str = Query("buy", enum=["buy", "sell"], description="Buy or sell rate"),
    current_user: User = Depends(get_current_user),
    service: ExchangeRateService = Depends(get_exchange_rate_service),
):
    """Get EUR to CRC exchange rate."""
    use_buy = rate_type == "buy"
    rate = await service.get_eur_rate(rate_date, use_buy_rate=use_buy)

    return {
        "currency": "EUR",
        "base_currency": "CRC",
        "rate": float(rate) if rate else None,
        "rate_type": rate_type,
        "date": (rate_date or date.today()).isoformat(),
        "source": "BCCR",
    }


@router.post("/convert", response_model=Dict[str, Any])
async def convert_currency(
    amount: Decimal = Query(..., gt=0, description="Amount to convert"),
    from_currency: SupportedCurrency = Query(..., description="Source currency"),
    to_currency: SupportedCurrency = Query(SupportedCurrency.CRC, description="Target currency"),
    rate_date: Optional[date] = Query(None, description="Date for exchange rate"),
    current_user: User = Depends(get_current_user),
    service: ExchangeRateService = Depends(get_exchange_rate_service),
):
    """
    Convert an amount between currencies.

    Uses BCCR rates for conversion through CRC as intermediate currency.
    """
    effective_date = rate_date or date.today()

    # Convert to CRC first if source is not CRC
    if from_currency == SupportedCurrency.CRC:
        crc_amount = amount
        from_rate = Decimal("1")
    else:
        conversion = await service.convert_to_crc(amount, from_currency, effective_date)
        crc_amount = conversion.converted_amount or amount
        from_rate = conversion.exchange_rate or Decimal("1")

    # Convert from CRC to target if target is not CRC
    if to_currency == SupportedCurrency.CRC:
        final_amount = crc_amount
        to_rate = Decimal("1")
    else:
        conversion = await service.convert_from_crc(crc_amount, to_currency, effective_date)
        final_amount = conversion.converted_amount or crc_amount
        to_rate = conversion.exchange_rate or Decimal("1")

    return {
        "original_amount": float(amount),
        "original_currency": from_currency.value,
        "converted_amount": float(final_amount),
        "converted_currency": to_currency.value,
        "exchange_rate": {
            "from_to_crc": float(from_rate),
            "crc_to_target": float(to_rate) if to_currency != SupportedCurrency.CRC else None,
        },
        "date": effective_date.isoformat(),
        "source": "BCCR",
    }


@router.get("/format", response_model=Dict[str, str])
async def format_currency_amount(
    amount: Decimal = Query(..., description="Amount to format"),
    currency: SupportedCurrency = Query(SupportedCurrency.CRC, description="Currency"),
    locale: str = Query("es", enum=["es", "en"], description="Locale for formatting"),
    current_user: User = Depends(get_current_user),
    service: ExchangeRateService = Depends(get_exchange_rate_service),
):
    """Format an amount with currency symbol and locale-specific formatting."""
    formatted = service.format_currency(amount, currency, locale)

    return {
        "amount": str(amount),
        "currency": currency.value,
        "formatted": formatted,
        "locale": locale,
    }
