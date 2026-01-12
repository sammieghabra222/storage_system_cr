"""Abstract repository interfaces for data access."""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List
from uuid import UUID

from app.domain.models import (
    Tenant, TenantCreate, TenantUpdate,
    User, UserCreate, UserUpdate,
    StorageUnit, StorageUnitCreate, StorageUnitUpdate,
    Customer, CustomerCreate, CustomerUpdate,
    Contract, ContractCreate, ContractUpdate,
    Invoice, InvoiceCreate, InvoiceUpdate,
    Payment, PaymentCreate,
)

T = TypeVar("T")
CreateT = TypeVar("CreateT")
UpdateT = TypeVar("UpdateT")


class AbstractRepository(ABC, Generic[T, CreateT, UpdateT]):
    """Base abstract repository with common CRUD operations."""

    @abstractmethod
    async def get_by_id(self, id: UUID) -> Optional[T]:
        """Get entity by ID."""
        pass

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities with pagination."""
        pass

    @abstractmethod
    async def create(self, entity: CreateT) -> T:
        """Create a new entity."""
        pass

    @abstractmethod
    async def update(self, id: UUID, entity: UpdateT) -> Optional[T]:
        """Update an existing entity."""
        pass

    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        """Delete an entity. Returns True if deleted, False if not found."""
        pass

    @abstractmethod
    async def count(self) -> int:
        """Count total entities."""
        pass


class AbstractTenantScopedRepository(AbstractRepository[T, CreateT, UpdateT], Generic[T, CreateT, UpdateT]):
    """Repository for tenant-scoped entities."""

    @abstractmethod
    async def get_by_id_for_tenant(self, id: UUID, tenant_id: UUID) -> Optional[T]:
        """Get entity by ID within a tenant scope."""
        pass

    @abstractmethod
    async def get_all_for_tenant(self, tenant_id: UUID, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities for a specific tenant."""
        pass

    @abstractmethod
    async def create_for_tenant(self, tenant_id: UUID, entity: CreateT) -> T:
        """Create entity within tenant scope."""
        pass

    @abstractmethod
    async def count_for_tenant(self, tenant_id: UUID) -> int:
        """Count entities for a tenant."""
        pass


class AbstractTenantRepository(AbstractRepository[Tenant, TenantCreate, TenantUpdate]):
    """Repository interface for tenants."""

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[Tenant]:
        """Get tenant by email."""
        pass

    @abstractmethod
    async def get_by_cedula_juridica(self, cedula: str) -> Optional[Tenant]:
        """Get tenant by business ID."""
        pass


class AbstractUserRepository(AbstractTenantScopedRepository[User, UserCreate, UserUpdate]):
    """Repository interface for users."""

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email (across all tenants for login)."""
        pass

    @abstractmethod
    async def get_by_email_for_tenant(self, email: str, tenant_id: UUID) -> Optional[User]:
        """Get user by email within tenant."""
        pass


class AbstractStorageUnitRepository(AbstractTenantScopedRepository[StorageUnit, StorageUnitCreate, StorageUnitUpdate]):
    """Repository interface for storage units."""

    @abstractmethod
    async def get_by_unit_number(self, unit_number: str, tenant_id: UUID) -> Optional[StorageUnit]:
        """Get unit by number within tenant."""
        pass

    @abstractmethod
    async def get_available_units(self, tenant_id: UUID) -> List[StorageUnit]:
        """Get all available units for tenant."""
        pass

    @abstractmethod
    async def get_by_status(self, tenant_id: UUID, status: str) -> List[StorageUnit]:
        """Get units by status."""
        pass


class AbstractCustomerRepository(AbstractTenantScopedRepository[Customer, CustomerCreate, CustomerUpdate]):
    """Repository interface for customers."""

    @abstractmethod
    async def get_by_email(self, email: str, tenant_id: UUID) -> Optional[Customer]:
        """Get customer by email within tenant."""
        pass

    @abstractmethod
    async def get_by_cedula(self, cedula: str, tenant_id: UUID) -> Optional[Customer]:
        """Get customer by national ID within tenant."""
        pass

    @abstractmethod
    async def search(self, tenant_id: UUID, query: str, skip: int = 0, limit: int = 20) -> List[Customer]:
        """Search customers by name, email, or phone."""
        pass


class AbstractContractRepository(AbstractTenantScopedRepository[Contract, ContractCreate, ContractUpdate]):
    """Repository interface for contracts."""

    @abstractmethod
    async def get_by_customer(self, customer_id: UUID, tenant_id: UUID) -> List[Contract]:
        """Get all contracts for a customer."""
        pass

    @abstractmethod
    async def get_by_unit(self, unit_id: UUID, tenant_id: UUID) -> List[Contract]:
        """Get all contracts for a unit."""
        pass

    @abstractmethod
    async def get_active_for_unit(self, unit_id: UUID, tenant_id: UUID) -> Optional[Contract]:
        """Get active contract for a unit."""
        pass

    @abstractmethod
    async def get_by_status(self, tenant_id: UUID, status: str) -> List[Contract]:
        """Get contracts by status."""
        pass


class AbstractInvoiceRepository(AbstractTenantScopedRepository[Invoice, InvoiceCreate, InvoiceUpdate]):
    """Repository interface for invoices."""

    @abstractmethod
    async def get_by_customer(self, customer_id: UUID, tenant_id: UUID) -> List[Invoice]:
        """Get all invoices for a customer."""
        pass

    @abstractmethod
    async def get_by_contract(self, contract_id: UUID, tenant_id: UUID) -> List[Invoice]:
        """Get all invoices for a contract."""
        pass

    @abstractmethod
    async def get_by_status(self, tenant_id: UUID, status: str) -> List[Invoice]:
        """Get invoices by status."""
        pass

    @abstractmethod
    async def get_overdue(self, tenant_id: UUID) -> List[Invoice]:
        """Get all overdue invoices."""
        pass

    @abstractmethod
    async def get_next_invoice_number(self, tenant_id: UUID) -> str:
        """Generate next invoice number for tenant."""
        pass


class AbstractPaymentRepository(AbstractTenantScopedRepository[Payment, PaymentCreate, None]):
    """Repository interface for payments."""

    @abstractmethod
    async def get_by_customer(self, customer_id: UUID, tenant_id: UUID) -> List[Payment]:
        """Get all payments for a customer."""
        pass

    @abstractmethod
    async def get_by_invoice(self, invoice_id: UUID, tenant_id: UUID) -> List[Payment]:
        """Get all payments for an invoice."""
        pass

    @abstractmethod
    async def get_pending(self, tenant_id: UUID) -> List[Payment]:
        """Get pending payments awaiting confirmation."""
        pass

    @abstractmethod
    async def get_next_payment_number(self, tenant_id: UUID) -> str:
        """Generate next payment number for tenant."""
        pass
