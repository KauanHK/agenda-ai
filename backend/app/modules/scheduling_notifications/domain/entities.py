import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.core.types import UNSET, BaseCreateCommand, BaseUpdateCommand, Unset
from app.modules.scheduling_notifications.domain.enums import NotificationStatus


@dataclass(frozen=True, slots=True)
class NewSchedulingNotification(BaseCreateCommand):
    establishment_id: uuid.UUID
    scheduling_id: uuid.UUID
    scheduled_at: datetime
    template_id: uuid.UUID | None = None
    status: NotificationStatus = NotificationStatus.pending


@dataclass(frozen=True, slots=True)
class UpdateSchedulingNotification(BaseUpdateCommand):
    status: NotificationStatus | Unset = UNSET
    content_at_send: str | None | Unset = UNSET
    sent_at: datetime | None | Unset = UNSET
    attempts: int | Unset = UNSET
    last_attempt_at: datetime | None | Unset = UNSET
    last_error: str | None | Unset = UNSET


@dataclass(frozen=True, slots=True)
class SchedulingNotification:
    id: uuid.UUID
    establishment_id: uuid.UUID
    scheduling_id: uuid.UUID
    template_id: uuid.UUID | None
    scheduled_at: datetime
    status: NotificationStatus
    content_at_send: str | None
    sent_at: datetime | None
    attempts: int
    last_attempt_at: datetime | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "establishment_id": self.establishment_id,
            "scheduling_id": self.scheduling_id,
            "template_id": self.template_id,
            "scheduled_at": self.scheduled_at,
            "status": self.status,
            "content_at_send": self.content_at_send,
            "sent_at": self.sent_at,
            "attempts": self.attempts,
            "last_attempt_at": self.last_attempt_at,
            "last_error": self.last_error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
