"""In-memory repository implementations for development and testing."""
from datetime import datetime, date
from typing import Dict, List, Optional, TypeVar, Generic
from uuid import UUID, uuid4

from app.domain.models import (
    Tenant, TenantCreate, TenantUpdate,
    User, UserCreate, UserUpdate,
    StorageUnit, StorageUnitCreate, StorageUnitUpdate, UnitStatus,
    Customer, CustomerCreate, CustomerUpdate,
    Contract, ContractCreate, ContractUpdate, ContractStatus,
    Invoice, InvoiceCreate, InvoiceUpdate, InvoiceStatus,
    Payment, PaymentCreate, PaymentStatus,
)
from app.infrastructure.repositories.base import (
    AbstractTenantRepository,
    AbstractUserRepository,
    AbstractStorageUnitRepository,
    AbstractCustomerRepository,
    AbstractContractRepository,
    AbstractInvoiceRepository,
    AbstractPaymentRepository,
)

T = TypeVar("T")


class MemoryTenantRepository(AbstractTenantRepository):
    """In-memory tenant repository."""

    def __init__(self):
        self._storage: Dict[UUID, Tenant] = {}

    async def get_by_id(self, id: UUID) -> Optional[Tenant]:
        return self._storage.get(id)

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Tenant]:
        tenants = list(self._storage.values())
        return tenants[skip : skip + limit]

    async def create(self, entity: TenantCreate) -> Tenant:
        tenant = Tenant(
            id=uuid4(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            **entity.model_dump()
        )
        self._storage[tenant.id] = tenant
        return tenant

    async def update(self, id: UUID, entity: TenantUpdate) -> Optional[Tenant]:
        if id not in self._storage:
            return None
        existing = self._storage[id]
        update_data = entity.model_dump(exclude_unset=True)
        updated = existing.model_copy(update={"updated_at": datetime.utcnow(), **update_data})
        self._storage[id] = updated
        return updated

    async def delete(self, id: UUID) -> bool:
        if id in self._storage:
            del self._storage[id]
            return True
        return False

    async def count(self) -> int:
        return len(self._storage)

    async def get_by_email(self, email: str) -> Optional[Tenant]:
        for tenant in self._storage.values():
            if tenant.email == email:
                return tenant
        return None

    async def get_by_cedula_juridica(self, cedula: str) -> Optional[Tenant]:
        for tenant in self._storage.values():
            if tenant.cedula_juridica == cedula:
                return tenant
        return None


class MemoryUserRepository(AbstractUserRepository):
    """In-memory user repository."""

    def __init__(self):
        self._storage: Dict[UUID, User] = {}

    async def get_by_id(self, id: UUID) -> Optional[User]:
        return self._storage.get(id)

    async def get_by_id_for_tenant(self, id: UUID, tenant_id: UUID) -> Optional[User]:
        user = self._storage.get(id)
        if user and user.tenant_id == tenant_id:
            return user
        return None

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        users = list(self._storage.values())
        return users[skip : skip + limit]

    async def get_all_for_tenant(self, tenant_id: UUID, skip: int = 0, limit: int = 100) -> List[User]:
        users = [u for u in self._storage.values() if u.tenant_id == tenant_id]
        return users[skip : skip + limit]

    async def create(self, entity: UserCreate) -> User:
        user = User(
            id=uuid4(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            tenant_id=entity.tenant_id,
            email=entity.email,
            first_name=entity.first_name,
            last_name=entity.last_name,
            phone=entity.phone,
            role=entity.role,
            is_active=entity.is_active,
            locale=entity.locale,
            hashed_password=entity.password,  # Will be hashed by security module
        )
        self._storage[user.id] = user
        return user

    async def create_for_tenant(self, tenant_id: UUID, entity: UserCreate) -> User:
        entity.tenant_id = tenant_id
        return await self.create(entity)

    async def update(self, id: UUID, entity: UserUpdate) -> Optional[User]:
        if id not in self._storage:
            return None
        existing = self._storage[id]
        update_data = entity.model_dump(exclude_unset=True)
        updated = existing.model_copy(update={"updated_at": datetime.utcnow(), **update_data})
        self._storage[id] = updated
        return updated

    async def delete(self, id: UUID) -> bool:
        if id in self._storage:
            del self._storage[id]
            return True
        return False

    async def count(self) -> int:
        return len(self._storage)

    async def count_for_tenant(self, tenant_id: UUID) -> int:
        return len([u for u in self._storage.values() if u.tenant_id == tenant_id])

    async def get_by_email(self, email: str) -> Optional[User]:
        for user in self._storage.values():
            if user.email == email:
                return user
        return None

    async def get_by_email_for_tenant(self, email: str, tenant_id: UUID) -> Optional[User]:
        for user in self._storage.values():
            if user.email == email and user.tenant_id == tenant_id:
                return user
        return None


class MemoryStorageUnitRepository(AbstractStorageUnitRepository):
    """In-memory storage unit repository."""

    def __init__(self):
        self._storage: Dict[UUID, StorageUnit] = {}

    async def get_by_id(self, id: UUID) -> Optional[StorageUnit]:
        return self._storage.get(id)

    async def get_by_id_for_tenant(self, id: UUID, tenant_id: UUID) -> Optional[StorageUnit]:
        unit = self._storage.get(id)
        if unit and unit.tenant_id == tenant_id:
            return unit
        return None

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[StorageUnit]:
        units = list(self._storage.values())
        return units[skip : skip + limit]

    async def get_all_for_tenant(self, tenant_id: UUID, skip: int = 0, limit: int = 100) -> List[StorageUnit]:
        units = [u for u in self._storage.values() if u.tenant_id == tenant_id]
        return units[skip : skip + limit]

    async def create(self, entity: StorageUnitCreate) -> StorageUnit:
        raise NotImplementedError("Use create_for_tenant instead")

    async def create_for_tenant(self, tenant_id: UUID, entity: StorageUnitCreate) -> StorageUnit:
        unit = StorageUnit(
            id=uuid4(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            tenant_id=tenant_id,
            **entity.model_dump()
        )
        self._storage[unit.id] = unit
        return unit

    async def update(self, id: UUID, entity: StorageUnitUpdate) -> Optional[StorageUnit]:
        if id not in self._storage:
            return None
        existing = self._storage[id]
        update_data = entity.model_dump(exclude_unset=True)
        updated = existing.model_copy(update={"updated_at": datetime.utcnow(), **update_data})
        self._storage[id] = updated
        return updated

    async def delete(self, id: UUID) -> bool:
        if id in self._storage:
            del self._storage[id]
            return True
        return False

    async def count(self) -> int:
        return len(self._storage)

    async def count_for_tenant(self, tenant_id: UUID) -> int:
        return len([u for u in self._storage.values() if u.tenant_id == tenant_id])

    async def get_by_unit_number(self, unit_number: str, tenant_id: UUID) -> Optional[StorageUnit]:
        for unit in self._storage.values():
            if unit.unit_number == unit_number and unit.tenant_id == tenant_id:
                return unit
        return None

    async def get_available_units(self, tenant_id: UUID) -> List[StorageUnit]:
        return [u for u in self._storage.values()
                if u.tenant_id == tenant_id and u.status == UnitStatus.AVAILABLE]

    async def get_by_status(self, tenant_id: UUID, status: str) -> List[StorageUnit]:
        return [u for u in self._storage.values()
                if u.tenant_id == tenant_id and u.status == status]


class MemoryCustomerRepository(AbstractCustomerRepository):
    """In-memory customer repository."""

    def __init__(self):
        self._storage: Dict[UUID, Customer] = {}

    async def get_by_id(self, id: UUID) -> Optional[Customer]:
        return self._storage.get(id)

    async def get_by_id_for_tenant(self, id: UUID, tenant_id: UUID) -> Optional[Customer]:
        customer = self._storage.get(id)
        if customer and customer.tenant_id == tenant_id:
            return customer
        return None

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Customer]:
        customers = list(self._storage.values())
        return customers[skip : skip + limit]

    async def get_all_for_tenant(self, tenant_id: UUID, skip: int = 0, limit: int = 100) -> List[Customer]:
        customers = [c for c in self._storage.values() if c.tenant_id == tenant_id]
        return customers[skip : skip + limit]

    async def create(self, entity: CustomerCreate) -> Customer:
        raise NotImplementedError("Use create_for_tenant instead")

    async def create_for_tenant(self, tenant_id: UUID, entity: CustomerCreate) -> Customer:
        customer = Customer(
            id=uuid4(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            tenant_id=tenant_id,
            **entity.model_dump()
        )
        self._storage[customer.id] = customer
        return customer

    async def update(self, id: UUID, entity: CustomerUpdate) -> Optional[Customer]:
        if id not in self._storage:
            return None
        existing = self._storage[id]
        update_data = entity.model_dump(exclude_unset=True)
        updated = existing.model_copy(update={"updated_at": datetime.utcnow(), **update_data})
        self._storage[id] = updated
        return updated

    async def delete(self, id: UUID) -> bool:
        if id in self._storage:
            del self._storage[id]
            return True
        return False

    async def count(self) -> int:
        return len(self._storage)

    async def count_for_tenant(self, tenant_id: UUID) -> int:
        return len([c for c in self._storage.values() if c.tenant_id == tenant_id])

    async def get_by_email(self, email: str, tenant_id: UUID) -> Optional[Customer]:
        for customer in self._storage.values():
            if customer.email == email and customer.tenant_id == tenant_id:
                return customer
        return None

    async def get_by_cedula(self, cedula: str, tenant_id: UUID) -> Optional[Customer]:
        for customer in self._storage.values():
            if customer.cedula == cedula and customer.tenant_id == tenant_id:
                return customer
        return None

    async def search(self, tenant_id: UUID, query: str, skip: int = 0, limit: int = 20) -> List[Customer]:
        query_lower = query.lower()
        results = []
        for customer in self._storage.values():
            if customer.tenant_id != tenant_id:
                continue
            if (query_lower in customer.first_name.lower() or
                (customer.last_name and query_lower in customer.last_name.lower()) or
                query_lower in customer.email.lower() or
                query_lower in customer.phone):
                results.append(customer)
        return results[skip : skip + limit]


class MemoryContractRepository(AbstractContractRepository):
    """In-memory contract repository."""

    def __init__(self):
        self._storage: Dict[UUID, Contract] = {}
        self._counter: Dict[UUID, int] = {}  # tenant_id -> contract count

    async def get_by_id(self, id: UUID) -> Optional[Contract]:
        return self._storage.get(id)

    async def get_by_id_for_tenant(self, id: UUID, tenant_id: UUID) -> Optional[Contract]:
        contract = self._storage.get(id)
        if contract and contract.tenant_id == tenant_id:
            return contract
        return None

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Contract]:
        contracts = list(self._storage.values())
        return contracts[skip : skip + limit]

    async def get_all_for_tenant(self, tenant_id: UUID, skip: int = 0, limit: int = 100) -> List[Contract]:
        contracts = [c for c in self._storage.values() if c.tenant_id == tenant_id]
        return contracts[skip : skip + limit]

    async def create(self, entity: ContractCreate) -> Contract:
        raise NotImplementedError("Use create_for_tenant instead")

    async def create_for_tenant(self, tenant_id: UUID, entity: ContractCreate) -> Contract:
        # Generate contract number if not provided
        contract_number = entity.contract_number
        if not contract_number:
            self._counter.setdefault(tenant_id, 0)
            self._counter[tenant_id] += 1
            contract_number = f"CTR-{self._counter[tenant_id]:06d}"

        contract = Contract(
            id=uuid4(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            tenant_id=tenant_id,
            contract_number=contract_number,
            customer_id=entity.customer_id,
            unit_id=entity.unit_id,
            status=ContractStatus.DRAFT,
            start_date=entity.start_date,
            end_date=entity.end_date,
            monthly_rate=entity.monthly_rate,
            deposit_amount=entity.deposit_amount,
            billing_cycle=entity.billing_cycle,
            billing_day=entity.billing_day,
            grace_period_days=entity.grace_period_days,
            late_fee_amount=entity.late_fee_amount,
            late_fee_percent=entity.late_fee_percent,
            auto_renew=entity.auto_renew,
            discount_percent=entity.discount_percent,
            discount_reason=entity.discount_reason,
            requires_insurance=entity.requires_insurance,
            access_code=entity.access_code,
            access_hours=entity.access_hours,
            special_terms=entity.special_terms,
            internal_notes=entity.internal_notes,
        )
        self._storage[contract.id] = contract
        return contract

    async def update(self, id: UUID, entity: ContractUpdate) -> Optional[Contract]:
        if id not in self._storage:
            return None
        existing = self._storage[id]
        update_data = entity.model_dump(exclude_unset=True)
        updated = existing.model_copy(update={"updated_at": datetime.utcnow(), **update_data})
        self._storage[id] = updated
        return updated

    async def delete(self, id: UUID) -> bool:
        if id in self._storage:
            del self._storage[id]
            return True
        return False

    async def count(self) -> int:
        return len(self._storage)

    async def count_for_tenant(self, tenant_id: UUID) -> int:
        return len([c for c in self._storage.values() if c.tenant_id == tenant_id])

    async def get_by_customer(self, customer_id: UUID, tenant_id: UUID) -> List[Contract]:
        return [c for c in self._storage.values()
                if c.customer_id == customer_id and c.tenant_id == tenant_id]

    async def get_by_unit(self, unit_id: UUID, tenant_id: UUID) -> List[Contract]:
        return [c for c in self._storage.values()
                if c.unit_id == unit_id and c.tenant_id == tenant_id]

    async def get_active_for_unit(self, unit_id: UUID, tenant_id: UUID) -> Optional[Contract]:
        for contract in self._storage.values():
            if (contract.unit_id == unit_id and
                contract.tenant_id == tenant_id and
                contract.status == ContractStatus.ACTIVE):
                return contract
        return None

    async def get_by_status(self, tenant_id: UUID, status: str) -> List[Contract]:
        return [c for c in self._storage.values()
                if c.tenant_id == tenant_id and c.status == status]


class MemoryInvoiceRepository(AbstractInvoiceRepository):
    """In-memory invoice repository."""

    def __init__(self):
        self._storage: Dict[UUID, Invoice] = {}
        self._counter: Dict[UUID, int] = {}

    async def get_by_id(self, id: UUID) -> Optional[Invoice]:
        return self._storage.get(id)

    async def get_by_id_for_tenant(self, id: UUID, tenant_id: UUID) -> Optional[Invoice]:
        invoice = self._storage.get(id)
        if invoice and invoice.tenant_id == tenant_id:
            return invoice
        return None

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Invoice]:
        invoices = list(self._storage.values())
        return invoices[skip : skip + limit]

    async def get_all_for_tenant(self, tenant_id: UUID, skip: int = 0, limit: int = 100) -> List[Invoice]:
        invoices = [i for i in self._storage.values() if i.tenant_id == tenant_id]
        return invoices[skip : skip + limit]

    async def create(self, entity: InvoiceCreate) -> Invoice:
        raise NotImplementedError("Use create_for_tenant instead")

    async def create_for_tenant(self, tenant_id: UUID, entity: InvoiceCreate) -> Invoice:
        invoice_number = entity.invoice_number or await self.get_next_invoice_number(tenant_id)

        invoice = Invoice(
            id=uuid4(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            tenant_id=tenant_id,
            customer_id=entity.customer_id,
            contract_id=entity.contract_id,
            invoice_number=invoice_number,
            status=InvoiceStatus.DRAFT,
            issue_date=entity.issue_date,
            due_date=entity.due_date,
            period_start=entity.period_start,
            period_end=entity.period_end,
            line_items=entity.line_items,
            currency=entity.currency,
            notes=entity.notes,
            internal_notes=entity.internal_notes,
        )
        invoice.recalculate_totals()
        self._storage[invoice.id] = invoice
        return invoice

    async def update(self, id: UUID, entity: InvoiceUpdate) -> Optional[Invoice]:
        if id not in self._storage:
            return None
        existing = self._storage[id]
        update_data = entity.model_dump(exclude_unset=True)
        updated = existing.model_copy(update={"updated_at": datetime.utcnow(), **update_data})
        if entity.line_items is not None:
            updated.recalculate_totals()
        self._storage[id] = updated
        return updated

    async def delete(self, id: UUID) -> bool:
        if id in self._storage:
            del self._storage[id]
            return True
        return False

    async def count(self) -> int:
        return len(self._storage)

    async def count_for_tenant(self, tenant_id: UUID) -> int:
        return len([i for i in self._storage.values() if i.tenant_id == tenant_id])

    async def get_by_customer(self, customer_id: UUID, tenant_id: UUID) -> List[Invoice]:
        return [i for i in self._storage.values()
                if i.customer_id == customer_id and i.tenant_id == tenant_id]

    async def get_by_contract(self, contract_id: UUID, tenant_id: UUID) -> List[Invoice]:
        return [i for i in self._storage.values()
                if i.contract_id == contract_id and i.tenant_id == tenant_id]

    async def get_by_status(self, tenant_id: UUID, status: str) -> List[Invoice]:
        return [i for i in self._storage.values()
                if i.tenant_id == tenant_id and i.status == status]

    async def get_overdue(self, tenant_id: UUID) -> List[Invoice]:
        today = date.today()
        return [i for i in self._storage.values()
                if i.tenant_id == tenant_id and
                i.due_date < today and
                i.status not in (InvoiceStatus.PAID, InvoiceStatus.CANCELLED, InvoiceStatus.REFUNDED)]

    async def get_next_invoice_number(self, tenant_id: UUID) -> str:
        self._counter.setdefault(tenant_id, 0)
        self._counter[tenant_id] += 1
        year = date.today().year
        return f"INV-{year}-{self._counter[tenant_id]:06d}"


class MemoryPaymentRepository(AbstractPaymentRepository):
    """In-memory payment repository."""

    def __init__(self):
        self._storage: Dict[UUID, Payment] = {}
        self._counter: Dict[UUID, int] = {}

    async def get_by_id(self, id: UUID) -> Optional[Payment]:
        return self._storage.get(id)

    async def get_by_id_for_tenant(self, id: UUID, tenant_id: UUID) -> Optional[Payment]:
        payment = self._storage.get(id)
        if payment and payment.tenant_id == tenant_id:
            return payment
        return None

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Payment]:
        payments = list(self._storage.values())
        return payments[skip : skip + limit]

    async def get_all_for_tenant(self, tenant_id: UUID, skip: int = 0, limit: int = 100) -> List[Payment]:
        payments = [p for p in self._storage.values() if p.tenant_id == tenant_id]
        return payments[skip : skip + limit]

    async def create(self, entity: PaymentCreate) -> Payment:
        raise NotImplementedError("Use create_for_tenant instead")

    async def create_for_tenant(self, tenant_id: UUID, entity: PaymentCreate) -> Payment:
        payment_number = await self.get_next_payment_number(tenant_id)

        payment = Payment(
            id=uuid4(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            tenant_id=tenant_id,
            customer_id=entity.customer_id,
            invoice_id=entity.invoice_id,
            payment_number=payment_number,
            method=entity.method,
            status=PaymentStatus.PENDING,
            amount=entity.amount,
            currency=entity.currency,
            payment_date=entity.payment_date or datetime.utcnow(),
            reference_number=entity.reference_number,
            sinpe_phone=entity.sinpe_phone,
            sinpe_confirmation=entity.sinpe_confirmation,
            notes=entity.notes,
        )
        self._storage[payment.id] = payment
        return payment

    async def update(self, id: UUID, entity) -> Optional[Payment]:
        if id not in self._storage:
            return None
        existing = self._storage[id]
        if entity:
            update_data = entity.model_dump(exclude_unset=True)
            updated = existing.model_copy(update={"updated_at": datetime.utcnow(), **update_data})
        else:
            updated = existing.model_copy(update={"updated_at": datetime.utcnow()})
        self._storage[id] = updated
        return updated

    async def delete(self, id: UUID) -> bool:
        if id in self._storage:
            del self._storage[id]
            return True
        return False

    async def count(self) -> int:
        return len(self._storage)

    async def count_for_tenant(self, tenant_id: UUID) -> int:
        return len([p for p in self._storage.values() if p.tenant_id == tenant_id])

    async def get_by_customer(self, customer_id: UUID, tenant_id: UUID) -> List[Payment]:
        return [p for p in self._storage.values()
                if p.customer_id == customer_id and p.tenant_id == tenant_id]

    async def get_by_invoice(self, invoice_id: UUID, tenant_id: UUID) -> List[Payment]:
        return [p for p in self._storage.values()
                if p.invoice_id == invoice_id and p.tenant_id == tenant_id]

    async def get_pending(self, tenant_id: UUID) -> List[Payment]:
        return [p for p in self._storage.values()
                if p.tenant_id == tenant_id and p.status == PaymentStatus.PENDING]

    async def get_next_payment_number(self, tenant_id: UUID) -> str:
        self._counter.setdefault(tenant_id, 0)
        self._counter[tenant_id] += 1
        year = date.today().year
        return f"PAY-{year}-{self._counter[tenant_id]:06d}"


class MemoryRepositoryManager:
    """Manager for all in-memory repositories."""

    def __init__(self):
        self.tenants = MemoryTenantRepository()
        self.users = MemoryUserRepository()
        self.storage_units = MemoryStorageUnitRepository()
        self.customers = MemoryCustomerRepository()
        self.contracts = MemoryContractRepository()
        self.invoices = MemoryInvoiceRepository()
        self.payments = MemoryPaymentRepository()
