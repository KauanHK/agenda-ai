import uuid
from datetime import datetime

from pydantic import UUID7

from app.core.schemas import BaseSchema
from app.modules.common.domain.schemas import EstablishmentScoped, TimestampMixin
from app.modules.scheduling_notifications.domain.enums import NotificationStatus


class SchedulingNotificationRead(BaseSchema, EstablishmentScoped, TimestampMixin):
    id: UUID7
    scheduling_id: uuid.UUID
    template_id: uuid.UUID | None
    scheduled_at: datetime
    status: NotificationStatus
    content_at_send: str | None
    sent_at: datetime | None
    attempts: int
    last_attempt_at: datetime | None
    last_error: str | None
