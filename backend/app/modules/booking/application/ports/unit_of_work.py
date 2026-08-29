from types import TracebackType
from typing import Protocol, Self

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.clients.adapters.db.repository import ClientsRepository
from app.modules.establishments.adapters.db.repository import EstablishmentsRepository
from app.modules.memberships.adapters.db.repository import MembershipsRepository
from app.modules.operating_hours.adapters.db.repository import OperatingHoursRepository
from app.modules.schedulings.infra.repository import SchedulingsRepository
from app.modules.services.infra.repository import ServicesRepository
from app.modules.unavailabilities.adapters.db.repository import (
    UnavailabilitiesRepository,
)


class BookingUnitOfWorkProtocol(Protocol):
    """
    Contrato da unidade de trabalho do agendamento pelo canal automático.

    Agrupa os repositórios de vários módulos porque marcar um horário é, por natureza,
    uma operação que cruza agregados: valida serviço e expediente, procura um
    profissional livre, grava o agendamento e enfileira as notificações — tudo em uma
    transação só.
    """

    @property
    def clients(self) -> ClientsRepository: ...

    @property
    def establishments(self) -> EstablishmentsRepository: ...

    @property
    def memberships(self) -> MembershipsRepository: ...

    @property
    def operating_hours(self) -> OperatingHoursRepository: ...

    @property
    def schedulings(self) -> SchedulingsRepository: ...

    @property
    def services(self) -> ServicesRepository: ...

    @property
    def unavailabilities(self) -> UnavailabilitiesRepository: ...

    @property
    def session(self) -> AsyncSession: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...
