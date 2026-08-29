from dataclasses import dataclass
from datetime import datetime

from app.core.types import UNSET, BaseCreateCommand, BaseUpdateCommand, Unset


@dataclass(frozen=True, slots=True)
class CreateUnavailabilityCommand(BaseCreateCommand):
    starts_at: datetime
    ends_at: datetime
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class UpdateUnavailabilityCommand(BaseUpdateCommand):
    starts_at: datetime | Unset = UNSET
    ends_at: datetime | Unset = UNSET
    reason: str | None | Unset = UNSET
