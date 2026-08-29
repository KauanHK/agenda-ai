import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.core.types import UNSET, BaseCreateCommand, BaseUpdateCommand, Unset
from app.modules.establishments.domain.enums import DocumentType


@dataclass(frozen=True, slots=True)
class NewEstablishment(BaseCreateCommand):
    name: str
    document: str
    document_type: DocumentType
    is_active: bool
    timezone: str
    street: str
    number: str
    complement: str | None
    neighborhood: str
    city: str
    state: str
    zip_code: str


@dataclass(frozen=True, slots=True)
class UpdateEstablishment(BaseUpdateCommand):
    name: str | Unset = UNSET
    document: str | Unset = UNSET
    timezone: str | Unset = UNSET
    street: str | Unset = UNSET
    number: str | Unset = UNSET
    complement: str | Unset = UNSET
    neighborhood: str | Unset = UNSET
    city: str | Unset = UNSET
    state: str | Unset = UNSET
    zip_code: str | Unset = UNSET
    is_active: bool | Unset = UNSET
    deleted_at: datetime | None | Unset = UNSET


@dataclass(frozen=True, slots=True)
class Establishment:
    id: uuid.UUID
    name: str
    document: str
    document_type: DocumentType
    timezone: str
    street: str
    number: str
    complement: str | None
    neighborhood: str
    city: str
    state: str
    zip_code: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "document": self.document,
            "document_type": self.document_type,
            "timezone": self.timezone,
            "street": self.street,
            "number": self.number,
            "complement": self.complement,
            "neighborhood": self.neighborhood,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
