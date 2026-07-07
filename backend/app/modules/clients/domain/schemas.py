from typing import Annotated

from pydantic import UUID7, EmailStr, Field

from app.modules.common.domain.schemas import (
    BaseSchema,
    EstablishmentScoped,
    TimestampMixin,
)

Name = Annotated[str, Field(min_length=1, max_length=255)]
Phone = Annotated[str, Field(min_length=1, max_length=32)]


class ClientBase(BaseSchema):
    name: Name
    phone: Phone
    email: EmailStr | None = None


class ClientRead(ClientBase, EstablishmentScoped, TimestampMixin):
    id: UUID7
    is_active: bool


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseSchema):
    name: Name | None = None
    phone: Phone | None = None
    email: EmailStr | None = None
    is_active: bool | None = None
