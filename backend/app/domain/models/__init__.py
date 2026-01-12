"""Domain models for the storage management platform."""
from app.domain.models.tenant import Tenant, TenantCreate, TenantUpdate
from app.domain.models.user import User, UserCreate, UserUpdate, UserRole
from app.domain.models.storage_unit import StorageUnit, StorageUnitCreate, StorageUnitUpdate, UnitType, UnitStatus
from app.domain.models.customer import Customer, CustomerCreate, CustomerUpdate
from app.domain.models.contract import Contract, ContractCreate, ContractUpdate, ContractStatus
from app.domain.models.invoice import Invoice, InvoiceCreate, InvoiceUpdate, InvoiceStatus
from app.domain.models.payment import Payment, PaymentCreate, PaymentMethod, PaymentStatus
from app.domain.models.currency import (
    SupportedCurrency,
    ExchangeRate,
    ExchangeRateCreate,
    ExchangeRateSource,
    CurrencyAmount,
    CurrencyConfig,
)
from app.domain.models.tax import (
    TarifaIVA,
    TaxCategory,
    TaxConfig,
    TaxConfigCreate,
    TaxConfigUpdate,
    TaxCalculation,
    TaxSummary,
    TaxExemptionReason,
    IVA_RATES,
)

__all__ = [
    "Tenant", "TenantCreate", "TenantUpdate",
    "User", "UserCreate", "UserUpdate", "UserRole",
    "StorageUnit", "StorageUnitCreate", "StorageUnitUpdate", "UnitType", "UnitStatus",
    "Customer", "CustomerCreate", "CustomerUpdate",
    "Contract", "ContractCreate", "ContractUpdate", "ContractStatus",
    "Invoice", "InvoiceCreate", "InvoiceUpdate", "InvoiceStatus",
    "Payment", "PaymentCreate", "PaymentMethod", "PaymentStatus",
    "SupportedCurrency", "ExchangeRate", "ExchangeRateCreate", "ExchangeRateSource",
    "CurrencyAmount", "CurrencyConfig",
    "TarifaIVA", "TaxCategory", "TaxConfig", "TaxConfigCreate", "TaxConfigUpdate",
    "TaxCalculation", "TaxSummary", "TaxExemptionReason", "IVA_RATES",
]
