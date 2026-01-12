"""FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.v1 import auth, tenants, storage_units, customers, contracts, invoices, payments, analytics, exchange_rates, tax
from app.core.middleware import TenantContextMiddleware
from app.infrastructure.repositories.memory import MemoryRepositoryManager

settings = get_settings()

# Global repository manager (will be injected via dependency)
repository_manager = MemoryRepositoryManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup: Initialize repositories, seed data if needed
    yield
    # Shutdown: Cleanup resources


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Storage management platform for Latin American markets",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.add_middleware(TenantContextMiddleware)

# API routes
app.include_router(auth.router, prefix=f"{settings.api_v1_prefix}/auth", tags=["Authentication"])
app.include_router(tenants.router, prefix=f"{settings.api_v1_prefix}/tenants", tags=["Tenants"])
app.include_router(storage_units.router, prefix=f"{settings.api_v1_prefix}/units", tags=["Storage Units"])
app.include_router(customers.router, prefix=f"{settings.api_v1_prefix}/customers", tags=["Customers"])
app.include_router(contracts.router, prefix=f"{settings.api_v1_prefix}/contracts", tags=["Contracts"])
app.include_router(invoices.router, prefix=f"{settings.api_v1_prefix}/invoices", tags=["Invoices"])
app.include_router(payments.router, prefix=f"{settings.api_v1_prefix}/payments", tags=["Payments"])
app.include_router(analytics.router, prefix=settings.api_v1_prefix, tags=["Analytics"])
app.include_router(exchange_rates.router, prefix=settings.api_v1_prefix, tags=["Exchange Rates"])
app.include_router(tax.router, prefix=settings.api_v1_prefix, tags=["Tax"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.app_version}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else "Disabled in production",
    }
