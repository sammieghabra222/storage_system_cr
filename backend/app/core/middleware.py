"""Application middleware."""
from contextvars import ContextVar
from typing import Optional
from uuid import UUID

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# Context variable for current tenant
current_tenant_id: ContextVar[Optional[UUID]] = ContextVar("current_tenant_id", default=None)
current_user_id: ContextVar[Optional[UUID]] = ContextVar("current_user_id", default=None)


def get_current_tenant_id() -> Optional[UUID]:
    """Get the current tenant ID from context."""
    return current_tenant_id.get()


def get_current_user_id() -> Optional[UUID]:
    """Get the current user ID from context."""
    return current_user_id.get()


class TenantContextMiddleware(BaseHTTPMiddleware):
    """Middleware to set tenant context from JWT token."""

    async def dispatch(self, request: Request, call_next):
        # Tenant context is set by the dependency injection when processing the request
        # This middleware can be extended for logging, metrics, etc.
        response = await call_next(request)
        return response
