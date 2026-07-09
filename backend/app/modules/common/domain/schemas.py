"""Compat: a `BaseSchema` agora vive em `app.core.schemas`. Re-export para imports
antigos."""

from datetime import datetime

from pydantic import UUID7, BaseModel

from app.core.schemas import BaseSchema

__all__ = ["BaseSchema", "EstablishmentScoped", "TimestampMixin"]


class TimestampMixin(BaseModel):
    created_at: datetime
    updated_at: datetime


class EstablishmentScoped(BaseModel):
    establishment_id: UUID7
