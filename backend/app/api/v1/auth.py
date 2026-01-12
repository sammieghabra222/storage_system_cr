"""Authentication endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from app.core.security import (
    hash_password,
    verify_password,
    create_token_pair,
    verify_token,
    TokenPair,
)
from app.dependencies import Repos, CurrentUser, get_current_token
from app.domain.models import User, UserCreate, UserRole, Tenant, TenantCreate

router = APIRouter()


class LoginRequest(BaseModel):
    """Login request schema."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class RegisterRequest(BaseModel):
    """Registration request for new tenant and owner."""

    # Tenant info
    business_name: str = Field(..., min_length=1, max_length=255)
    business_email: EmailStr
    business_phone: str = Field(None, max_length=20)

    # Owner info
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)

    # Optional
    locale: str = Field(default="es")


class RefreshRequest(BaseModel):
    """Token refresh request."""

    refresh_token: str


class UserResponse(BaseModel):
    """User response schema."""

    id: str
    email: str
    first_name: str
    last_name: str
    role: str
    tenant_id: str
    locale: str

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    """Authentication response with tokens and user info."""

    tokens: TokenPair
    user: UserResponse


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, repos: Repos):
    """Register a new tenant and owner account."""
    # Check if email already exists
    existing_user = await repos.users.get_by_email(request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Check if business email already exists
    existing_tenant = await repos.tenants.get_by_email(request.business_email)
    if existing_tenant:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Business email already registered",
        )

    # Create tenant
    tenant = await repos.tenants.create(
        TenantCreate(
            name=request.business_name,
            email=request.business_email,
            phone=request.business_phone,
            locale=request.locale,
        )
    )

    # Create owner user
    user = await repos.users.create(
        UserCreate(
            tenant_id=tenant.id,
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name,
            password=hash_password(request.password),
            role=UserRole.OWNER,
            locale=request.locale,
        )
    )

    # Generate tokens
    tokens = create_token_pair(user.id, tenant.id, user.email, user.role.value)

    return AuthResponse(
        tokens=tokens,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role.value,
            tenant_id=str(user.tenant_id),
            locale=user.locale,
        ),
    )


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, repos: Repos):
    """Login with email and password."""
    # Find user by email
    user = await repos.users.get_by_email(request.email)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled",
        )

    # Verify password
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Generate tokens
    tokens = create_token_pair(user.id, user.tenant_id, user.email, user.role.value)

    return AuthResponse(
        tokens=tokens,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role.value,
            tenant_id=str(user.tenant_id),
            locale=user.locale,
        ),
    )


@router.post("/refresh", response_model=TokenPair)
async def refresh_token(request: RefreshRequest, repos: Repos):
    """Refresh access token using refresh token."""
    payload = verify_token(request.refresh_token, token_type="refresh")

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Verify user still exists and is active
    from uuid import UUID
    user = await repos.users.get_by_id(UUID(payload.sub))

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found or disabled",
        )

    # Generate new tokens
    return create_token_pair(user.id, user.tenant_id, user.email, user.role.value)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(user: CurrentUser):
    """Get current user information."""
    return UserResponse(
        id=str(user.id),
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role.value,
        tenant_id=str(user.tenant_id),
        locale=user.locale,
    )
