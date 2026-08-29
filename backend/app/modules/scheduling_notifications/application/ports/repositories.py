from typing import Protocol

from app.core.db.ports import BaseRepositoryProtocol
from app.modules.scheduling_notifications.application.dtos.filters import (
    SchedulingNotificationFilters,
)
from app.modules.scheduling_notifications.domain.entities import (
    NewSchedulingNotification,
    SchedulingNotification,
    UpdateSchedulingNotification,
)


class SchedulingNotificationsRepositoryProtocol(
    BaseRepositoryProtocol[
        SchedulingNotification,
        SchedulingNotificationFilters,
        NewSchedulingNotification,
        UpdateSchedulingNotification,
    ],
    Protocol,
):
    async def get_pending_due(
        self, limit: int = 100
    ) -> list[SchedulingNotification]: ...
