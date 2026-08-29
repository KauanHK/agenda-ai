import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.core.types import UNSET, BaseCreateCommand, BaseUpdateCommand, Unset


@dataclass(frozen=True, slots=True)
class NewUnavailability(BaseCreateCommand):
    establishment_id: uuid.UUID
    starts_at: datetime
    ends_at: datetime
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class UpdateUnavailability(BaseUpdateCommand):
    starts_at: datetime | Unset = UNSET
    ends_at: datetime | Unset = UNSET
    reason: str | None | Unset = UNSET


@dataclass(frozen=True, slots=True)
class Unavailability:
    id: uuid.UUID
    establishment_id: uuid.UUID
    starts_at: datetime
    ends_at: datetime
    reason: str | None
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "establishment_id": self.establishment_id,
            "starts_at": self.starts_at,
            "ends_at": self.ends_at,
            "reason": self.reason,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
