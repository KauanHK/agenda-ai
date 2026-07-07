import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.pagination import PaginationParams
from app.modules.scheduling_notifications.domain.enums import NotificationStatus
from app.modules.scheduling_notifications.domain.filters import (
    SchedulingNotificationFilters,
)
from app.modules.scheduling_notifications.domain.model import SchedulingNotification


class SchedulingNotificationsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id_or_none(self, notification_id: uuid.UUID) -> SchedulingNotification | None:
        return await self._session.get(SchedulingNotification, notification_id)

    async def get_by_id(self, notification_id: uuid.UUID) -> SchedulingNotification:
        notification = await self.get_by_id_or_none(notification_id)
        if notification is None:
            raise NotFoundError("Notificação não encontrada.")
        return notification

    async def update(self, notification: SchedulingNotification) -> SchedulingNotification:
        merged = await self._session.merge(notification)
        await self._session.flush()
        await self._session.refresh(merged)
        return merged

    async def list(
        self,
        pagination: PaginationParams,
        filters: SchedulingNotificationFilters | None = None,
    ) -> list[SchedulingNotification]:
        query = self._construct_select_query(filters)
        query = query.limit(pagination.size).offset(pagination.offset)
        result = await self._session.execute(query)
        return list(result.scalars())

    async def count(self, filters: SchedulingNotificationFilters | None = None) -> int:
        query = select(func.count()).select_from(  # pylint: disable=not-callable
            self._construct_select_query(filters).subquery()
        )
        result = await self._session.execute(query)
        return result.scalar_one()

    async def get_pending_due(self, limit: int = 100) -> list[SchedulingNotification]:
        now = datetime.now(UTC)
        query = (
            select(SchedulingNotification)
            .where(SchedulingNotification.status == NotificationStatus.pending)
            .where(SchedulingNotification.scheduled_at <= now)
            .limit(limit)
        )
        result = await self._session.execute(query)
        return list(result.scalars())

    def _construct_select_query(
        self,
        filters: SchedulingNotificationFilters | None = None,
    ) -> Select[tuple[SchedulingNotification]]:
        query = select(SchedulingNotification)
        if filters is None:
            return query
        if filters.establishment_id is not None:
            query = query.where(SchedulingNotification.establishment_id == filters.establishment_id)
        if filters.scheduling_id is not None:
            query = query.where(SchedulingNotification.scheduling_id == filters.scheduling_id)
        if filters.template_id is not None:
            query = query.where(SchedulingNotification.template_id == filters.template_id)
        if filters.status is not None:
            query = query.where(SchedulingNotification.status == filters.status)
        if filters.sent_at_from is not None:
            query = query.where(SchedulingNotification.sent_at >= filters.sent_at_from)
        if filters.sent_at_to is not None:
            query = query.where(SchedulingNotification.sent_at <= filters.sent_at_to)
        return query
