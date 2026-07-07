import uuid

from app.core.actors.user import UserActor
from app.core.exceptions import NotFoundError, ValidationAppError
from app.db.unit_of_work import UnitOfWork
from app.modules.scheduling_notifications.application._authz import assert_can_write
from app.modules.scheduling_notifications.domain.enums import NotificationStatus
from app.modules.scheduling_notifications.domain.model import SchedulingNotification
from app.modules.scheduling_notifications.domain.schemas import (
    SchedulingNotificationRead,
)
from app.modules.scheduling_notifications.infra.repository import (
    SchedulingNotificationsRepository,
)


class SchedulingNotificationsCanceller:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def cancel(
        self,
        notification_id: uuid.UUID,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> SchedulingNotificationRead:
        assert_can_write(actor, establishment_id)
        async with self._uow:
            repo = self._uow.repository(SchedulingNotificationsRepository)
            notification = await repo.get_by_id(notification_id)
            self._assert_scope(notification, establishment_id)

            if notification.status != NotificationStatus.pending:
                raise ValidationAppError(
                    "Apenas notificações pendentes podem ser canceladas."
                )

            notification.status = NotificationStatus.cancelled
            notification = await repo.update(notification)
            return SchedulingNotificationRead.model_validate(notification)

    def _assert_scope(
        self, notification: SchedulingNotification, establishment_id: uuid.UUID
    ) -> None:
        if notification.establishment_id != establishment_id:
            raise NotFoundError("Notificação não encontrada.")
