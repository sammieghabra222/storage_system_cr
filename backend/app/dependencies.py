"""Dependency injection for FastAPI."""
from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import verify_token, TokenPayload
from app.core.middleware import current_tenant_id, current_user_id
from app.domain.models import User, UserRole
from app.infrastructure.repositories.memory import MemoryRepositoryManager

# Security scheme
security = HTTPBearer()

# Global repository manager (singleton for in-memory)
_repository_manager: Optional[MemoryRepositoryManager] = None


def get_repository_manager() -> MemoryRepositoryManager:
    """Get the repository manager instance."""
    global _repository_manager
    if _repository_manager is None:
        _repository_manager = MemoryRepositoryManager()
    return _repository_manager


async def get_current_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> TokenPayload:
    """Validate and return the current token payload."""
    token = credentials.credentials
    payload = verify_token(token, token_type="access")

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Set context variables
    current_tenant_id.set(UUID(payload.tenant_id))
    current_user_id.set(UUID(payload.sub))

    return payload


async def get_current_user(
    token: Annotated[TokenPayload, Depends(get_current_token)],
    repos: Annotated[MemoryRepositoryManager, Depends(get_repository_manager)],
) -> User:
    """Get the current authenticated user."""
    user = await repos.users.get_by_id(UUID(token.sub))

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
        )

    return user


async def get_current_tenant_id_dep(
    token: Annotated[TokenPayload, Depends(get_current_token)]
) -> UUID:
    """Get the current tenant ID from the token."""
    return UUID(token.tenant_id)


def require_role(*allowed_roles: UserRole):
    """Dependency factory to require specific roles."""

    async def role_checker(
        user: Annotated[User, Depends(get_current_user)]
    ) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' is not authorized for this action",
            )
        return user

    return role_checker


# Common dependencies
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentTenantId = Annotated[UUID, Depends(get_current_tenant_id_dep)]
Repos = Annotated[MemoryRepositoryManager, Depends(get_repository_manager)]

# Role-based dependencies
OwnerUser = Annotated[User, Depends(require_role(UserRole.OWNER))]
ManagerUser = Annotated[User, Depends(require_role(UserRole.OWNER, UserRole.MANAGER))]
StaffUser = Annotated[User, Depends(require_role(UserRole.OWNER, UserRole.MANAGER, UserRole.STAFF))]


# Service dependencies
def get_billing_service(
    repos: Annotated[MemoryRepositoryManager, Depends(get_repository_manager)]
):
    """Get the billing service instance."""
    from app.domain.services.billing_service import BillingService
    return BillingService(
        contract_repo=repos.contracts,
        invoice_repo=repos.invoices,
        customer_repo=repos.customers,
    )


def get_notification_service(
    repos: Annotated[MemoryRepositoryManager, Depends(get_repository_manager)]
):
    """Get the notification service instance."""
    from app.domain.services.notification_service import NotificationService
    return NotificationService(
        customer_repo=repos.customers,
        invoice_repo=repos.invoices,
        contract_repo=repos.contracts,
        tenant_repo=repos.tenants,
    )


def get_analytics_service(
    repos: Annotated[MemoryRepositoryManager, Depends(get_repository_manager)]
):
    """Get the analytics service instance."""
    from app.domain.services.analytics_service import AnalyticsService
    return AnalyticsService(
        unit_repo=repos.units,
        contract_repo=repos.contracts,
        customer_repo=repos.customers,
        invoice_repo=repos.invoices,
        payment_repo=repos.payments,
    )
