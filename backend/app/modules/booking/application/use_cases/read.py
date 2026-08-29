"""Consultas do cliente: serviços oferecidos, horários livres e a própria agenda."""

import uuid
from datetime import UTC, date, datetime

from app.core.actors.customer import CustomerActor
from app.core.pagination import PaginationParams
from app.modules.booking.application.ports.unit_of_work import BookingUnitOfWorkProtocol
from app.modules.booking.application.use_cases.availability import (
    MAX_SLOTS,
    AvailabilityCalculator,
)
from app.modules.booking.domain.entities import (
    BookableService,
    CustomerScheduling,
    Slot,
)
from app.modules.booking.domain.exceptions import SchedulingNotFoundError
from app.modules.schedulings.domain.enums import SchedulingStatus
from app.modules.schedulings.domain.filters import SchedulingFilters
from app.modules.services.domain.filters import ServiceFilters

# Nenhum estabelecimento realista oferece mais que isso, e o resultado vai para o
# contexto de um LLM.
_MAX_SERVICES = 100

# Uma conversa lida com a agenda próxima; o histórico completo não interessa ao agente.
_MAX_SCHEDULINGS = 20


class BookingReader:
    def __init__(self, uow: BookingUnitOfWorkProtocol) -> None:
        self._uow = uow

    async def list_services(self, actor: CustomerActor) -> list[BookableService]:
        """
        Lista os serviços ativos do estabelecimento da sessão.

        Args:
            actor (CustomerActor): O cliente autenticado.

        Returns:
            list[BookableService]: Os serviços que o cliente pode agendar.
        """

        async with self._uow as uow:
            services = await uow.services.list(
                pagination=PaginationParams(page=1, size=_MAX_SERVICES),
                filters=ServiceFilters(
                    establishment_id=actor.establishment_id,
                    is_active=True,
                ),
            )

            return [
                BookableService(
                    id=service.id,
                    name=service.name,
                    description=service.description,
                    duration_minutes=service.duration_minutes,
                    price=service.price,
                )
                for service in services
            ]

    async def list_slots(
        self,
        actor: CustomerActor,
        service_id: uuid.UUID,
        target_date: date,
        limit: int = MAX_SLOTS,
    ) -> list[Slot]:
        """
        Lista os horários livres de um serviço em um dia.

        Args:
            actor (CustomerActor): O cliente autenticado.
            service_id (uuid.UUID): O serviço desejado.
            target_date (date): O dia, na data local do estabelecimento.
            limit (int): Máximo de horários devolvidos.

        Returns:
            list[Slot]: Os horários livres.
        """

        async with self._uow as uow:
            calculator = AvailabilityCalculator(uow)
            service = await calculator.get_bookable_service(
                establishment_id=actor.establishment_id,
                service_id=service_id,
            )
            slots = await calculator.free_slots(
                establishment_id=actor.establishment_id,
                service=service,
                target_date=target_date,
                client_id=actor.client_id,
                limit=limit,
            )

            timezone = await calculator.get_timezone(actor.establishment_id)
            return [slot.in_timezone(timezone) for slot in slots]

    async def list_schedulings(
        self,
        actor: CustomerActor,
    ) -> list[CustomerScheduling]:
        """
        Lista os agendamentos futuros e ainda válidos do cliente.

        Args:
            actor (CustomerActor): O cliente autenticado.

        Returns:
            list[CustomerScheduling]: Os agendamentos, em ordem cronológica.
        """

        async with self._uow as uow:
            schedulings = await uow.schedulings.list(
                pagination=PaginationParams(page=1, size=_MAX_SCHEDULINGS),
                filters=SchedulingFilters(
                    establishment_id=actor.establishment_id,
                    client_id=actor.client_id,
                    starts_at_from=datetime.now(UTC),
                ),
            )

            timezone = await AvailabilityCalculator(uow).get_timezone(
                actor.establishment_id
            )

            return [
                CustomerScheduling(
                    id=scheduling.id,
                    starts_at=scheduling.starts_at,
                    ends_at=scheduling.ends_at,
                    status=scheduling.status,
                    service_id=scheduling.service_id,
                    service_name=scheduling.service.name,
                ).in_timezone(timezone)
                for scheduling in schedulings
                if scheduling.status != SchedulingStatus.CANCELLED
            ]

    async def get_scheduling(
        self,
        actor: CustomerActor,
        scheduling_id: uuid.UUID,
    ) -> CustomerScheduling:
        """
        Obtém um agendamento do próprio cliente.

        Args:
            actor (CustomerActor): O cliente autenticado.
            scheduling_id (uuid.UUID): O agendamento.

        Returns:
            CustomerScheduling: O agendamento.

        Raises:
            SchedulingNotFoundError:
                Se o agendamento não existe ou não é do cliente da sessão.
        """

        async with self._uow as uow:
            scheduling = await uow.schedulings.get_by_id_expanded(scheduling_id)
            if (
                scheduling is None
                or scheduling.client_id != actor.client_id
                or scheduling.establishment_id != actor.establishment_id
            ):
                raise SchedulingNotFoundError()

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
