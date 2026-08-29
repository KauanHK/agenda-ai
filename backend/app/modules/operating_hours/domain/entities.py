import uuid
from dataclasses import dataclass
from datetime import time
from typing import Any

from app.core.types import UNSET, BaseCreateCommand, BaseUpdateCommand, Unset


@dataclass(frozen=True, slots=True)
class NewOperatingHour(BaseCreateCommand):
    establishment_id: uuid.UUID
    weekday: int
    start_time: time
    end_time: time


@dataclass(frozen=True, slots=True)
class UpdateOperatingHour(BaseUpdateCommand):
    weekday: int | Unset = UNSET
    start_time: time | Unset = UNSET
    end_time: time | Unset = UNSET


@dataclass(frozen=True, slots=True)
class OperatingHour:
    id: uuid.UUID
    establishment_id: uuid.UUID
    weekday: int
    start_time: time
    end_time: time

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "establishment_id": self.establishment_id,
            "weekday": self.weekday,
            "start_time": self.start_time,
            "end_time": self.end_time,
        }
