"""Reagendamento pelo próprio cliente."""

import uuid
from datetime import datetime, timedelta

from app.core.actors.customer import CustomerActor
from app.db.unit_of_work import UnitOfWork as LegacyUnitOfWork
from app.modules.booking.application.ports.unit_of_work import BookingUnitOfWorkProtocol
from app.modules.booking.application.use_cases._notifications import (
    cancel_pending_notifications,
)
from app.modules.booking.application.use_cases.availability import (
    AvailabilityCalculator,
)
from app.modules.booking.application.use_cases.cancel import TERMINAL_STATUSES
from app.modules.booking.domain.entities import CustomerScheduling
from app.modules.booking.domain.exceptions import (
    SchedulingNotChangeableError,
    SchedulingNotFoundError,
)
from app.modules.scheduling_notifications.application.use_cases.create import (
    SchedulingNotificationsCreator,
)


class BookingRescheduler:
    def __init__(self, uow: BookingUnitOfWorkProtocol) -> None:
        self._uow = uow

    async def reschedule(
        self,
        actor: CustomerActor,
        scheduling_id: uuid.UUID,
        new_starts_at: datetime,
    ) -> CustomerScheduling:
        """
        Move um agendamento do cliente para outro horário.

        O novo horário passa pelas mesmas validações de uma marcação nova, e o
        profissional é reatribuído — quem atendia antes pode não estar livre agora.
        As notificações já programadas são refeitas para o horário novo.

        Args:
            actor (CustomerActor): O cliente autenticado.
            scheduling_id (uuid.UUID): O agendamento a mover.
            new_starts_at (datetime):
                O novo início. Sem fuso, é interpretado no fuso do estabelecimento.

        Returns:
            CustomerScheduling: O agendamento no horário novo.

        Raises:
            SchedulingNotFoundError:
                Se o agendamento não existe ou não é do cliente da sessão.
            SchedulingNotChangeableError:
                Se o agendamento já foi cancelado ou concluído.
            PastDateTimeError | ClosedOnWeekdayError | OutsideOperatingHoursError |
            EstablishmentUnavailableError | NoProfessionalAvailableError |
            SchedulingOverlapClientError:
                Se o novo horário não está disponível. Ver `AvailabilityCalculator`.
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

            calculator = AvailabilityCalculator(uow)
            service = await calculator.get_bookable_service(
                establishment_id=actor.establishment_id,
                service_id=scheduling.service_id,
            )

            timezone = await calculator.get_timezone(actor.establishment_id)
            if new_starts_at.tzinfo is None:
                new_starts_at = new_starts_at.replace(tzinfo=timezone)

            user_id = await calculator.assign_professional(
                establishment_id=actor.establishment_id,
                service=service,
                starts_at=new_starts_at,
                client_id=actor.client_id,
                exclude_scheduling_id=scheduling.id,
            )

            scheduling.user_id = user_id
            scheduling.starts_at = new_starts_at
            scheduling.ends_at = new_starts_at + timedelta(
                minutes=service.duration_minutes
            )
            scheduling = await uow.schedulings.update(scheduling)

            # As notificações apontavam para o horário antigo; refaz a partir do novo.
            await cancel_pending_notifications(uow.session, scheduling.id)
            await uow.session.flush()
            await SchedulingNotificationsCreator(
                LegacyUnitOfWork(uow.session)
            ).create_for_scheduling(scheduling)

            return CustomerScheduling(
                id=scheduling.id,
                starts_at=scheduling.starts_at,
                ends_at=scheduling.ends_at,
                status=scheduling.status,
                service_id=service.id,
                service_name=service.name,
            ).in_timezone(timezone)
