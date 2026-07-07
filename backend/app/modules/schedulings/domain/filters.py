import uuid
from dataclasses import dataclass
from datetime import datetime

from app.modules.schedulings.domain.enums import SchedulingSource, SchedulingStatus


@dataclass
class SchedulingFilters:
    establishment_id: uuid.UUID | None = None
    status: SchedulingStatus | None = None
    source: SchedulingSource | None = None
    user_id: uuid.UUID | None = None
    client_id: uuid.UUID | None = None
    service_id: uuid.UUID | None = None
    starts_at_from: datetime | None = None
    starts_at_to: datetime | None = None
