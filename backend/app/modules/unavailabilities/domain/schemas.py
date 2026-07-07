from datetime import datetime
from typing import Annotated

from pydantic import UUID7, Field

from app.modules.common.domain.schemas import (
    BaseSchema,
    EstablishmentScoped,
    TimestampMixin,
)

Reason = Annotated[str | None, Field(max_length=500)]


class UnavailabilityCreate(BaseSchema):
    starts_at: datetime
    ends_at: datetime
    reason: Reason = None


class UnavailabilityUpdate(BaseSchema):
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    reason: Reason = None


class UnavailabilityRead(BaseSchema, EstablishmentScoped, TimestampMixin):
    id: UUID7
    starts_at: datetime
    ends_at: datetime
    reason: str | None
