from dataclasses import dataclass
from datetime import datetime


@dataclass
class UnavailabilityFilters:
    starts_at_from: datetime | None = None
    starts_at_to: datetime | None = None
    establishment_id: str | None = None
