import uuid

from app.core.actors.user import UserActor
from app.core.exceptions import NotFoundError
from app.core.pagination import (
    PaginatedResponse,
    PaginationParams,
    build_paginated_response,
)
from app.db.unit_of_work import UnitOfWork
from app.modules.scheduling_notifications.application._authz import assert_can_access
from app.modules.scheduling_notifications.domain.filters import (
    SchedulingNotificationFilters,
)
from app.modules.scheduling_notifications.domain.model import SchedulingNotification
from app.modules.scheduling_notifications.domain.schemas import (
    SchedulingNotificationRead,
)
from app.modules.scheduling_notifications.infra.repository import (
    SchedulingNotificationsRepository,
)


class SchedulingNotificationsReader:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def get_by_id(
        self,
        notification_id: uuid.UUID,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> SchedulingNotificationRead:
        assert_can_access(actor, establishment_id)
        async with self._uow:
            repo = self._uow.repository(SchedulingNotificationsRepository)
            notification = await repo.get_by_id(notification_id)
            self._assert_scope(notification, establishment_id)
            return SchedulingNotificationRead.model_validate(notification)

    async def paginate(
        self,
        pagination: PaginationParams,
        actor: UserActor,
        establishment_id: uuid.UUID,
        filters: SchedulingNotificationFilters | None = None,
    ) -> PaginatedResponse[SchedulingNotificationRead]:
        assert_can_access(actor, establishment_id)
        filters = filters or SchedulingNotificationFilters()
        scoped = SchedulingNotificationFilters(
            establishment_id=establishment_id,
            scheduling_id=filters.scheduling_id,
            template_id=filters.template_id,
            status=filters.status,
            sent_at_from=filters.sent_at_from,
            sent_at_to=filters.sent_at_to,
        )
        async with self._uow:
            repo = self._uow.repository(SchedulingNotificationsRepository)
            notifications = await repo.list(pagination=pagination, filters=scoped)
            total = await repo.count(filters=scoped)
            return build_paginated_response(
                items=[
                    SchedulingNotificationRead.model_validate(n) for n in notifications
                ],
                total=total,
                params=pagination,
            )

    def _assert_scope(
        self, notification: SchedulingNotification, establishment_id: uuid.UUID
    ) -> None:
        if notification.establishment_id != establishment_id:
            raise NotFoundError("Notificação não encontrada.")
