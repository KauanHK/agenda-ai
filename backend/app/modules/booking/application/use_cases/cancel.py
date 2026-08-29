"""Cancelamento de agendamento pelo próprio cliente."""

import uuid

from app.core.actors.customer import CustomerActor
from app.modules.booking.application.ports.unit_of_work import BookingUnitOfWorkProtocol
from app.modules.booking.application.use_cases._notifications import (
    cancel_pending_notifications,
)
from app.modules.booking.application.use_cases.availability import (
    AvailabilityCalculator,
)
from app.modules.booking.domain.entities import CustomerScheduling
from app.modules.booking.domain.exceptions import (
    SchedulingNotChangeableError,
    SchedulingNotFoundError,
)
from app.modules.schedulings.domain.enums import (
    CancelledByType,
    ChangedBySource,
    SchedulingStatus,
)
from app.modules.schedulings.domain.model import SchedulingStatusLog

TERMINAL_STATUSES = frozenset(
    {SchedulingStatus.CANCELLED, SchedulingStatus.COMPLETED}
)


class BookingCanceller:
    def __init__(self, uow: BookingUnitOfWorkProtocol) -> None:
        self._uow = uow

    async def cancel(
        self,
        actor: CustomerActor,
        scheduling_id: uuid.UUID,
    ) -> CustomerScheduling:
        """
        Cancela um agendamento do cliente da sessão.

        Args:
            actor (CustomerActor): O cliente autenticado.
            scheduling_id (uuid.UUID): O agendamento a cancelar.

        Returns:
            CustomerScheduling: O agendamento já cancelado.

        Raises:
            SchedulingNotFoundError:
                Se o agendamento não existe ou não é do cliente da sessão — a mesma
                exceção nos dois casos, para não revelar agendamentos de terceiros.
            SchedulingNotChangeableError:
                Se o agendamento já foi cancelado ou concluído.
        """

        async with self._uow as uow:
            scheduling = await uow.schedulings.get_by_id_expanded(scheduling_id)
            if (
                scheduling is None
                or scheduling.client_id != actor.client_id
                or scheduling.establishment_id != actor.establishment_id
            ):
                raise SchedulingNotFoundError()

            if scheduling.status in TERMINAL_STATUSES:
                raise SchedulingNotChangeableError()

            from_status = scheduling.status
            scheduling.status = SchedulingStatus.CANCELLED
            scheduling.cancelled_by_type = CancelledByType.CLIENT
            scheduling.cancelled_by_user_id = None
            await uow.schedulings.update(scheduling)

            uow.session.add(
                SchedulingStatusLog(
                    scheduling_id=scheduling.id,
                    from_status=from_status,
                    to_status=SchedulingStatus.CANCELLED,
                    changed_by_source=ChangedBySource.CLIENT,
                    changed_by_user_id=None,
                )
            )

            await cancel_pending_notifications(uow.session, scheduling.id)
            await uow.session.flush()

            timezone = await AvailabilityCalculator(uow).get_timezone(
                actor.establishment_id
            )

            return CustomerScheduling(
                id=scheduling.id,
                starts_at=scheduling.starts_at,
                ends_at=scheduling.ends_at,
                status=scheduling.status,
                service_id=scheduling.service_id,
                service_name=scheduling.service.name,
            ).in_timezone(timezone)
