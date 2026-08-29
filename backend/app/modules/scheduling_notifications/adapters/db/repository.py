from datetime import UTC, datetime
from typing import Any

import sqlalchemy as sa

from app.core.db.repository import BaseRepository
from app.modules.scheduling_notifications.adapters.db.models import (
    SchedulingNotification as SchedulingNotificationModel,
)
from app.modules.scheduling_notifications.application.dtos.filters import (
    SchedulingNotificationFilters,
)
from app.modules.scheduling_notifications.domain.entities import SchedulingNotification
from app.modules.scheduling_notifications.domain.enums import NotificationStatus


class SchedulingNotificationsRepository(
    BaseRepository[
        SchedulingNotificationModel,
        SchedulingNotification,
        SchedulingNotificationFilters,
    ]
):
    model = SchedulingNotificationModel
    filters_type = SchedulingNotificationFilters

    async def get_pending_due(self, limit: int = 100) -> list[SchedulingNotification]:
        """
        Lista as notificações pendentes cujo horário de envio já passou. Usado pelo
        worker Celery para despachar os envios.
        """

        now = datetime.now(UTC)
        stmt = (
            sa.select(self.model)
            .where(self.model.status == NotificationStatus.pending)
            .where(self.model.scheduled_at <= now)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(row) for row in result.scalars().all()]

    def _to_entity(self, row: SchedulingNotificationModel) -> SchedulingNotification:
        return SchedulingNotification(
            id=row.id,
            establishment_id=row.establishment_id,
            scheduling_id=row.scheduling_id,
            template_id=row.template_id,
            scheduled_at=row.scheduled_at,
            status=row.status,
            content_at_send=row.content_at_send,
            sent_at=row.sent_at,
            attempts=row.attempts,
            last_attempt_at=row.last_attempt_at,
            last_error=row.last_error,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _apply_filters(
        self,
        stmt: sa.Select[Any],
        filters: SchedulingNotificationFilters,
    ) -> sa.Select[Any]:
        if filters.establishment_id is not None:
            stmt = stmt.where(self.model.establishment_id == filters.establishment_id)
        if filters.scheduling_id is not None:
            stmt = stmt.where(self.model.scheduling_id == filters.scheduling_id)
        if filters.template_id is not None:
            stmt = stmt.where(self.model.template_id == filters.template_id)
        if filters.status is not None:
            stmt = stmt.where(self.model.status == filters.status)
        if filters.sent_at_from is not None:
            stmt = stmt.where(self.model.sent_at >= filters.sent_at_from)
        if filters.sent_at_to is not None:
            stmt = stmt.where(self.model.sent_at <= filters.sent_at_to)
        return stmt
