import uuid

from app.core.actors.user import UserActor
from app.core.exceptions import NotFoundError
from app.core.pagination.params import Page, PageParams
from app.modules.scheduling_notifications.application.authz import assert_can_access
from app.modules.scheduling_notifications.application.dtos.filters import (
    SchedulingNotificationFilters,
)
from app.modules.scheduling_notifications.application.ports.unit_of_work import (
    SchedulingNotificationsUnitOfWorkProtocol,
)
from app.modules.scheduling_notifications.domain.entities import SchedulingNotification


class SchedulingNotificationsReader:
    def __init__(self, uow: SchedulingNotificationsUnitOfWorkProtocol) -> None:
        """
        Inicializa um leitor de notificações de agendamento.

        Args:
            uow (SchedulingNotificationsUnitOfWorkProtocol):
                Unit of work de notificações de agendamento.
        """

        self._uow = uow

    async def get_by_id(
        self,
        notification_id: uuid.UUID,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> SchedulingNotification:
        """
        Obtém uma notificação de agendamento pelo seu id.

        Raises:
            NotFoundError:
                Se a notificação não existir ou pertencer a outro estabelecimento.
        """

        assert_can_access(actor, establishment_id)
        async with self._uow as uow:
            notification = await uow.scheduling_notifications.get_by_id(
                notification_id
            )
            self._assert_scope(notification, establishment_id)
            return notification

    async def paginate(
        self,
        page_params: PageParams,
        actor: UserActor,
        establishment_id: uuid.UUID,
        filters: SchedulingNotificationFilters | None = None,
    ) -> Page[SchedulingNotification]:
        """Pagina notificações de agendamento do estabelecimento, com filtros opcionais."""

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
        async with self._uow as uow:
            return await uow.scheduling_notifications.paginate(
                page_params=page_params,
                filters=scoped,
            )

    def _assert_scope(
        self,
        notification: SchedulingNotification,
        establishment_id: uuid.UUID,
    ) -> None:
        if notification.establishment_id != establishment_id:
            raise NotFoundError("Notificação não encontrada.")
