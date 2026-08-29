"""Criação de agendamento pelo cliente, através do canal automático."""

import uuid
from datetime import datetime, timedelta

from app.core.actors.customer import CustomerActor
from app.db.unit_of_work import UnitOfWork as LegacyUnitOfWork
from app.modules.booking.application.ports.unit_of_work import BookingUnitOfWorkProtocol
from app.modules.booking.application.use_cases.availability import (
    AvailabilityCalculator,
)
from app.modules.booking.domain.entities import CustomerScheduling
from app.modules.scheduling_notifications.application.use_cases.create import (
    SchedulingNotificationsCreator,
)
from app.modules.schedulings.domain.enums import (
    ChangedBySource,
    SchedulingSource,
    SchedulingStatus,
)
from app.modules.schedulings.domain.model import Scheduling, SchedulingStatusLog


class BookingCreator:
    def __init__(self, uow: BookingUnitOfWorkProtocol) -> None:
        self._uow = uow

    async def create(
        self,
        actor: CustomerActor,
        service_id: uuid.UUID,
        starts_at: datetime,
    ) -> CustomerScheduling:
        """
        Marca um agendamento para o cliente da sessão.

        O cliente e o estabelecimento vêm do token, nunca dos argumentos: o agente de
        IA escolhe apenas o serviço e o horário.

        Args:
            actor (CustomerActor): O cliente autenticado.
            service_id (uuid.UUID): O serviço escolhido.
            starts_at (datetime):
                O início desejado. Sem fuso, é interpretado no fuso do
                estabelecimento — que é o horário sobre o qual a conversa acontece.

        Returns:
            CustomerScheduling: O agendamento criado.

        Raises:
            ServiceUnavailableError: Se o serviço não pode ser agendado.
            PastDateTimeError | ClosedOnWeekdayError | OutsideOperatingHoursError |
            EstablishmentUnavailableError | NoProfessionalAvailableError |
            SchedulingOverlapClientError:
                Se o horário não está disponível. Ver `AvailabilityCalculator`.
        """

        async with self._uow as uow:
            calculator = AvailabilityCalculator(uow)

            service = await calculator.get_bookable_service(
                establishment_id=actor.establishment_id,
                service_id=service_id,
            )

            timezone = await calculator.get_timezone(actor.establishment_id)
            if starts_at.tzinfo is None:
                starts_at = starts_at.replace(tzinfo=timezone)

            user_id = await calculator.assign_professional(
                establishment_id=actor.establishment_id,
                service=service,
                starts_at=starts_at,
                client_id=actor.client_id,
            )

            ends_at = starts_at + timedelta(minutes=service.duration_minutes)

            scheduling = await uow.schedulings.create(
                Scheduling(
                    establishment_id=actor.establishment_id,
                    user_id=user_id,
                    client_id=actor.client_id,
                    service_id=service.id,
                    status=SchedulingStatus.PENDING,
                    source=SchedulingSource.WHATSAPP,
                    starts_at=starts_at,
                    ends_at=ends_at,
                )
            )

            uow.session.add(
                SchedulingStatusLog(
                    scheduling_id=scheduling.id,
                    from_status=None,
                    to_status=SchedulingStatus.PENDING,
                    changed_by_source=ChangedBySource.CLIENT,
                    changed_by_user_id=None,
                )
            )
            await uow.session.flush()

            # O criador de notificações é compartilhado com o painel e espera a UoW
            # genérica; envolvendo a mesma sessão, tudo fica na mesma transação.
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
