import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class UnavailabilityFilters:
    establishment_id: uuid.UUID | None = None
    starts_at_from: datetime | None = None
    starts_at_to: datetime | None = None
