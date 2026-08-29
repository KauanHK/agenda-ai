import uuid

from app.core.actors.user import UserActor
from app.core.exceptions import NotFoundError, ValidationAppError
from app.modules.scheduling_notifications.application.authz import assert_can_write
from app.modules.scheduling_notifications.application.ports.unit_of_work import (
    SchedulingNotificationsUnitOfWorkProtocol,
)
from app.modules.scheduling_notifications.domain.entities import (
    SchedulingNotification,
    UpdateSchedulingNotification,
)
from app.modules.scheduling_notifications.domain.enums import NotificationStatus


class SchedulingNotificationsCanceller:
    def __init__(self, uow: SchedulingNotificationsUnitOfWorkProtocol) -> None:
        """
        Inicializa um cancelador de notificações de agendamento.

        Args:
            uow (SchedulingNotificationsUnitOfWorkProtocol):
                Unit of work de notificações de agendamento.
        """

        self._uow = uow

    async def cancel(
        self,
        notification_id: uuid.UUID,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> SchedulingNotification:
        """
        Cancela uma notificação de agendamento pendente.

        Raises:
            NotFoundError:
                Se a notificação não existir ou pertencer a outro estabelecimento.
            ValidationAppError:
                Se a notificação não estiver pendente.
        """

        assert_can_write(actor, establishment_id)

        async with self._uow as uow:
            notification = await uow.scheduling_notifications.get_by_id(
                notification_id
            )
            self._assert_scope(notification, establishment_id)

            if notification.status != NotificationStatus.pending:
                raise ValidationAppError(
                    "Apenas notificações pendentes podem ser canceladas."
                )

            return await uow.scheduling_notifications.update(
                id_=notification_id,
                update_command=UpdateSchedulingNotification(
                    status=NotificationStatus.cancelled
                ),
            )

    def _assert_scope(
        self,
        notification: SchedulingNotification,
        establishment_id: uuid.UUID,
    ) -> None:
        if notification.establishment_id != establishment_id:
            raise NotFoundError("Notificação não encontrada.")
