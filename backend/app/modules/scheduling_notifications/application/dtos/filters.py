import uuid
from dataclasses import dataclass
from datetime import datetime

from app.modules.scheduling_notifications.domain.enums import NotificationStatus


@dataclass(frozen=True, slots=True)
class SchedulingNotificationFilters:
    establishment_id: uuid.UUID | None = None
    scheduling_id: uuid.UUID | None = None
    template_id: uuid.UUID | None = None
    status: NotificationStatus | None = None
    sent_at_from: datetime | None = None
    sent_at_to: datetime | None = None
