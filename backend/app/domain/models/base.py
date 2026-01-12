"""Base model with common fields."""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class BaseEntity(BaseModel):
    """Base entity with common fields for all domain models."""

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class TenantScopedEntity(BaseEntity):
    """Base entity that belongs to a tenant (multi-tenancy support)."""

    tenant_id: UUID
