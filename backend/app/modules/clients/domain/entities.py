import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.core.types import UNSET, BaseCreateCommand, BaseUpdateCommand, Unset


@dataclass(frozen=True, slots=True)
class NewClient(BaseCreateCommand):
    establishment_id: uuid.UUID
    name: str
    phone: str
    email: str | None
    is_active: bool = True


@dataclass(frozen=True, slots=True)
class UpdateClient(BaseUpdateCommand):
    name: str | Unset = UNSET
    phone: str | Unset = UNSET
    email: str | None | Unset = UNSET
    is_active: bool | Unset = UNSET
    deleted_at: datetime | None | Unset = UNSET


@dataclass(frozen=True, slots=True)
class Client:
    id: uuid.UUID
    establishment_id: uuid.UUID
    name: str
    phone: str
    email: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "establishment_id": self.establishment_id,
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
