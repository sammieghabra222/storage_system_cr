"""Custom exceptions for the application."""
from typing import Any, Optional


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        detail: Optional[Any] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.message)


class NotFoundError(AppException):
    """Resource not found."""

    def __init__(self, resource: str, id: Any = None):
        message = f"{resource} not found"
        if id:
            message = f"{resource} with ID {id} not found"
        super().__init__(message=message, status_code=404)


class ConflictError(AppException):
    """Resource already exists or conflict."""

    def __init__(self, message: str):
        super().__init__(message=message, status_code=409)


class ValidationError(AppException):
    """Validation error."""

    def __init__(self, message: str, detail: Optional[Any] = None):
        super().__init__(message=message, status_code=422, detail=detail)


class AuthenticationError(AppException):
    """Authentication failed."""

    def __init__(self, message: str = "Could not validate credentials"):
        super().__init__(message=message, status_code=401)


class AuthorizationError(AppException):
    """Not authorized to perform action."""

    def __init__(self, message: str = "Not authorized to perform this action"):
        super().__init__(message=message, status_code=403)


class TenantAccessError(AppException):
    """Tenant access violation."""

    def __init__(self, message: str = "Access to this resource is not allowed"):
        super().__init__(message=message, status_code=403)
