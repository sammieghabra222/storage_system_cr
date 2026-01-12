"""Exchange rate service with BCCR integration."""
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from uuid import UUID
import xml.etree.ElementTree as ET

import httpx

from app.domain.models.currency import (
    BCCR_INDICATORS,
    BCCRExchangeRateResponse,
    CurrencyAmount,
    ExchangeRate,
    ExchangeRateCreate,
    ExchangeRateSource,
    SupportedCurrency,
)

logger = logging.getLogger(__name__)


class ExchangeRateService:
    """Service for managing exchange rates and currency conversion."""

    # BCCR public web service URL
    BCCR_API_URL = "https://gee.bccr.fi.cr/Indicadores/Suscripciones/WS/wsindicadoreseconomicos.asmx/ObtenerIndicadoresEconomicosXML"

    # Cache exchange rates for performance (in-memory for now)
    _rate_cache: Dict[str, Tuple[Decimal, datetime]] = {}
    CACHE_DURATION = timedelta(hours=1)

    def __init__(self, exchange_rate_repository=None):
        self.exchange_rate_repo = exchange_rate_repository

    async def get_bccr_exchange_rate(
        self,
        indicator: str,
        rate_date: Optional[date] = None,
    ) -> Optional[BCCRExchangeRateResponse]:
        """
        Fetch exchange rate from BCCR public API.

        Args:
            indicator: BCCR indicator code (e.g., "317" for USD buy rate)
            rate_date: Date to get rate for (defaults to today)

        Returns:
            BCCRExchangeRateResponse or None if unavailable
        """
        if rate_date is None:
            rate_date = date.today()

        # Check cache first
        cache_key = f"{indicator}_{rate_date.isoformat()}"
        if cache_key in self._rate_cache:
            cached_value, cached_time = self._rate_cache[cache_key]
            if datetime.now() - cached_time < self.CACHE_DURATION:
                currency = "USD" if indicator in ("317", "318") else "EUR"
                return BCCRExchangeRateResponse(
                    indicator=indicator,
                    date=rate_date,
                    value=cached_value,
                    currency=currency,
                    description=f"Tipo de cambio {currency}",
                )

        try:
            # Format dates for BCCR API
            date_str = rate_date.strftime("%d/%m/%Y")

            params = {
                "Indicador": indicator,
                "FechaInicio": date_str,
                "FechaFinal": date_str,
                "Nombre": "StorageCR",  # Application identifier
                "SubNiveles": "N",
                "CorreoElectronico": "api@bodegacr.com",
                "Token": "",  # Public access, no token needed
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.BCCR_API_URL, params=params)
                response.raise_for_status()

                # Parse XML response
                root = ET.fromstring(response.text)

                # BCCR returns XML with structure like:
                # <Indicadores_economicos>
                #   <INGC011_CAT_INDICADORECONOMICO>
                #     <NUM_VALOR>645.12</NUM_VALOR>
                #     <DES_FECHA>2024-01-15</DES_FECHA>
                #   </INGC011_CAT_INDICADORECONOMICO>
                # </Indicadores_economicos>

                # Find the value in the XML
                ns = {"": "http://ws.sdde.bccr.fi.cr"}
                value_elem = root.find(".//NUM_VALOR", ns)

                if value_elem is not None and value_elem.text:
                    rate_value = Decimal(value_elem.text.replace(",", "."))

                    # Cache the result
                    self._rate_cache[cache_key] = (rate_value, datetime.now())

                    currency = "USD" if indicator in ("317", "318") else "EUR"
                    return BCCRExchangeRateResponse(
                        indicator=indicator,
                        date=rate_date,
                        value=rate_value,
                        currency=currency,
                        description=f"Tipo de cambio {currency}",
                    )

        except httpx.HTTPError as e:
            logger.error(f"BCCR API error: {e}")
        except ET.ParseError as e:
            logger.error(f"BCCR XML parse error: {e}")
        except Exception as e:
            logger.error(f"Exchange rate fetch error: {e}")

        return None

    async def get_usd_rate(
        self,
        rate_date: Optional[date] = None,
        use_buy_rate: bool = True,
    ) -> Optional[Decimal]:
        """
        Get USD to CRC exchange rate.

        Args:
            rate_date: Date for the rate
            use_buy_rate: True for buy rate, False for sell rate

        Returns:
            Exchange rate as Decimal or None
        """
        indicator = BCCR_INDICATORS["USD_BUY" if use_buy_rate else "USD_SELL"]
        result = await self.get_bccr_exchange_rate(indicator, rate_date)
        return result.value if result else None

    async def get_eur_rate(
        self,
        rate_date: Optional[date] = None,
        use_buy_rate: bool = True,
    ) -> Optional[Decimal]:
        """Get EUR to CRC exchange rate."""
        indicator = BCCR_INDICATORS["EUR_BUY" if use_buy_rate else "EUR_SELL"]
        result = await self.get_bccr_exchange_rate(indicator, rate_date)
        return result.value if result else None

    async def get_all_rates(
        self,
        rate_date: Optional[date] = None,
    ) -> Dict[str, Dict[str, Decimal]]:
        """
        Get all exchange rates for a date.

        Returns:
            Dict like {"USD": {"buy": 645.0, "sell": 650.0}, "EUR": {...}}
        """
        if rate_date is None:
            rate_date = date.today()

        rates = {}

        # Fetch USD rates
        usd_buy = await self.get_usd_rate(rate_date, use_buy_rate=True)
        usd_sell = await self.get_usd_rate(rate_date, use_buy_rate=False)
        if usd_buy or usd_sell:
            rates["USD"] = {}
            if usd_buy:
                rates["USD"]["buy"] = usd_buy
            if usd_sell:
                rates["USD"]["sell"] = usd_sell

        # Fetch EUR rates
        eur_buy = await self.get_eur_rate(rate_date, use_buy_rate=True)
        eur_sell = await self.get_eur_rate(rate_date, use_buy_rate=False)
        if eur_buy or eur_sell:
            rates["EUR"] = {}
            if eur_buy:
                rates["EUR"]["buy"] = eur_buy
            if eur_sell:
                rates["EUR"]["sell"] = eur_sell

        return rates

    async def convert_to_crc(
        self,
        amount: Decimal,
        from_currency: SupportedCurrency,
        rate_date: Optional[date] = None,
        use_buy_rate: bool = True,
    ) -> CurrencyAmount:
        """
        Convert an amount to CRC.

        Args:
            amount: Amount to convert
            from_currency: Source currency
            rate_date: Date for exchange rate
            use_buy_rate: Use buy rate (True) or sell rate (False)

        Returns:
            CurrencyAmount with conversion details
        """
        if from_currency == SupportedCurrency.CRC:
            return CurrencyAmount(
                amount=amount,
                currency=from_currency,
                converted_amount=amount,
                converted_currency=SupportedCurrency.CRC,
            )

        if rate_date is None:
            rate_date = date.today()

        rate = None
        if from_currency == SupportedCurrency.USD:
            rate = await self.get_usd_rate(rate_date, use_buy_rate)
        elif from_currency == SupportedCurrency.EUR:
            rate = await self.get_eur_rate(rate_date, use_buy_rate)

        if rate is None:
            # Fallback to stored rates or default
            rate = await self._get_fallback_rate(from_currency)

        converted = amount * rate if rate else amount

        return CurrencyAmount(
            amount=amount,
            currency=from_currency,
            converted_amount=converted.quantize(Decimal("0.01")),
            converted_currency=SupportedCurrency.CRC,
            exchange_rate=rate,
            exchange_rate_date=rate_date,
        )

    async def convert_from_crc(
        self,
        amount: Decimal,
        to_currency: SupportedCurrency,
        rate_date: Optional[date] = None,
        use_sell_rate: bool = True,
    ) -> CurrencyAmount:
        """
        Convert an amount from CRC to another currency.

        Args:
            amount: Amount in CRC
            to_currency: Target currency
            rate_date: Date for exchange rate
            use_sell_rate: Use sell rate (True) or buy rate (False)

        Returns:
            CurrencyAmount with conversion details
        """
        if to_currency == SupportedCurrency.CRC:
            return CurrencyAmount(
                amount=amount,
                currency=SupportedCurrency.CRC,
                converted_amount=amount,
                converted_currency=SupportedCurrency.CRC,
            )

        if rate_date is None:
            rate_date = date.today()

        rate = None
        if to_currency == SupportedCurrency.USD:
            rate = await self.get_usd_rate(rate_date, use_buy_rate=not use_sell_rate)
        elif to_currency == SupportedCurrency.EUR:
            rate = await self.get_eur_rate(rate_date, use_buy_rate=not use_sell_rate)

        if rate is None:
            rate = await self._get_fallback_rate(to_currency)

        converted = (amount / rate).quantize(Decimal("0.01")) if rate else amount

        return CurrencyAmount(
            amount=amount,
            currency=SupportedCurrency.CRC,
            converted_amount=converted,
            converted_currency=to_currency,
            exchange_rate=rate,
            exchange_rate_date=rate_date,
        )

    async def _get_fallback_rate(
        self,
        currency: SupportedCurrency,
    ) -> Optional[Decimal]:
        """Get fallback rate from repository or use conservative estimate."""
        # Try to get latest stored rate
        if self.exchange_rate_repo:
            stored_rates = await self.exchange_rate_repo.find_by(
                from_currency=currency.value,
                to_currency="CRC",
            )
            if stored_rates:
                # Return most recent
                return sorted(stored_rates, key=lambda r: r.rate_date, reverse=True)[0].rate

        # Conservative fallback estimates (should be updated)
        fallbacks = {
            SupportedCurrency.USD: Decimal("520.00"),  # Conservative USD/CRC rate
            SupportedCurrency.EUR: Decimal("560.00"),  # Conservative EUR/CRC rate
        }
        return fallbacks.get(currency)

    async def store_rate(
        self,
        tenant_id: UUID,
        rate: ExchangeRateCreate,
    ) -> ExchangeRate:
        """Store an exchange rate in the repository."""
        if not self.exchange_rate_repo:
            raise RuntimeError("Exchange rate repository not configured")

        exchange_rate = ExchangeRate(
            tenant_id=tenant_id,
            from_currency=rate.from_currency,
            to_currency=rate.to_currency,
            rate=rate.rate,
            rate_date=rate.rate_date,
            source=rate.source,
            is_buy_rate=rate.is_buy_rate,
        )
        return await self.exchange_rate_repo.create(exchange_rate)

    async def sync_bccr_rates(self, tenant_id: UUID) -> List[ExchangeRate]:
        """
        Fetch and store current BCCR rates.

        Returns:
            List of stored ExchangeRate records
        """
        stored_rates = []
        today = date.today()

        # Fetch and store USD rates
        usd_buy = await self.get_usd_rate(today, use_buy_rate=True)
        if usd_buy:
            rate_create = ExchangeRateCreate(
                from_currency="USD",
                to_currency="CRC",
                rate=usd_buy,
                rate_date=today,
                source=ExchangeRateSource.BCCR,
                is_buy_rate=True,
            )
            stored_rates.append(await self.store_rate(tenant_id, rate_create))

        usd_sell = await self.get_usd_rate(today, use_buy_rate=False)
        if usd_sell:
            rate_create = ExchangeRateCreate(
                from_currency="USD",
                to_currency="CRC",
                rate=usd_sell,
                rate_date=today,
                source=ExchangeRateSource.BCCR,
                is_buy_rate=False,
            )
            stored_rates.append(await self.store_rate(tenant_id, rate_create))

        # Fetch and store EUR rates
        eur_buy = await self.get_eur_rate(today, use_buy_rate=True)
        if eur_buy:
            rate_create = ExchangeRateCreate(
                from_currency="EUR",
                to_currency="CRC",
                rate=eur_buy,
                rate_date=today,
                source=ExchangeRateSource.BCCR,
                is_buy_rate=True,
            )
            stored_rates.append(await self.store_rate(tenant_id, rate_create))

        eur_sell = await self.get_eur_rate(today, use_buy_rate=False)
        if eur_sell:
            rate_create = ExchangeRateCreate(
                from_currency="EUR",
                to_currency="CRC",
                rate=eur_sell,
                rate_date=today,
                source=ExchangeRateSource.BCCR,
                is_buy_rate=False,
            )
            stored_rates.append(await self.store_rate(tenant_id, rate_create))

        return stored_rates

    def format_currency(
        self,
        amount: Decimal,
        currency: SupportedCurrency,
        locale: str = "es",
    ) -> str:
        """
        Format amount with currency symbol.

        Args:
            amount: Amount to format
            currency: Currency code
            locale: Locale for formatting (es or en)

        Returns:
            Formatted string like "₡1,234.56" or "$1,234.56"
        """
        symbols = {
            SupportedCurrency.CRC: "₡",
            SupportedCurrency.USD: "$",
            SupportedCurrency.EUR: "€",
        }

        symbol = symbols.get(currency, currency.value)

        # Format with thousands separator
        if locale == "es":
            # Spanish format: 1.234,56
            formatted = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        else:
            # English format: 1,234.56
            formatted = f"{amount:,.2f}"

        return f"{symbol}{formatted}"
