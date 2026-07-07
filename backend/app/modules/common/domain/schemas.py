from datetime import datetime

from pydantic import UUID7, BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base com config ORM-friendly."""

    model_config = ConfigDict(from_attributes=True)


class TimestampMixin(BaseModel):
    created_at: datetime
    updated_at: datetime


class EstablishmentScoped(BaseModel):
    establishment_id: UUID7
