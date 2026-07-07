import uuid
from decimal import Decimal
from typing import Annotated

from pydantic import UUID7, Field

from app.modules.common.domain.schemas import (
    BaseSchema,
    EstablishmentScoped,
    TimestampMixin,
)
from app.modules.services.domain.filters import ServiceFilters

Name = Annotated[str, Field(min_length=1, max_length=255)]
Description = Annotated[str, Field(max_length=1000)]
DurationMinutes = Annotated[int, Field(gt=0)]
Price = Annotated[Decimal, Field(ge=0, max_digits=10, decimal_places=2)]


class ServiceBase(BaseSchema):
    name: Name
    description: Description | None = None
    duration_minutes: DurationMinutes
    price: Price


class ServiceRead(ServiceBase, EstablishmentScoped, TimestampMixin):
    id: UUID7
    is_active: bool


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseSchema):
    name: Name | None = None
    description: Description | None = None
    duration_minutes: DurationMinutes | None = None
    price: Price | None = None
    is_active: bool | None = None


class ServicesQueryParams(BaseSchema):
    q: str | None = None
    is_active: bool | None = None

    def to_filters(
        self,
        establishment_id: uuid.UUID,
    ) -> ServiceFilters:

        return ServiceFilters(
            establishment_id=establishment_id,
            **self.model_dump(),
        )
