from collections.abc import Callable
from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.unit_of_work import BaseUnitOfWork
from app.modules.clients.adapters.db.repository import ClientsRepository
from app.modules.establishments.adapters.db.repository import EstablishmentsRepository
from app.modules.memberships.adapters.db.repository import MembershipsRepository
from app.modules.operating_hours.adapters.db.repository import OperatingHoursRepository
from app.modules.schedulings.infra.repository import SchedulingsRepository
from app.modules.services.infra.repository import ServicesRepository
from app.modules.unavailabilities.adapters.db.repository import (
    UnavailabilitiesRepository,
)


class BookingUnitOfWork(BaseUnitOfWork):
    """Unidade de trabalho do agendamento pelo canal automático."""

    def __init__(
        self,
        session_factory: Callable[[], AsyncSession],
    ) -> None:

        super().__init__(session_factory=session_factory)
        self._clients: ClientsRepository | None = None
        self._establishments: EstablishmentsRepository | None = None
        self._memberships: MembershipsRepository | None = None
        self._operating_hours: OperatingHoursRepository | None = None
        self._schedulings: SchedulingsRepository | None = None
        self._services: ServicesRepository | None = None
        self._unavailabilities: UnavailabilitiesRepository | None = None

    @property
    def clients(self) -> ClientsRepository:
        """Repositório de clientes."""
        return self._require(self._clients, "clientes")

    @property
    def establishments(self) -> EstablishmentsRepository:
        """Repositório de estabelecimentos."""
        return self._require(self._establishments, "estabelecimentos")

    @property
    def memberships(self) -> MembershipsRepository:
        """Repositório de memberships."""
        return self._require(self._memberships, "memberships")

    @property
    def operating_hours(self) -> OperatingHoursRepository:
        """Repositório de horários de funcionamento."""
        return self._require(self._operating_hours, "horários de funcionamento")

    @property
    def schedulings(self) -> SchedulingsRepository:
        """Repositório de agendamentos."""
        return self._require(self._schedulings, "agendamentos")

    @property
    def services(self) -> ServicesRepository:
        """Repositório de serviços."""
        return self._require(self._services, "serviços")

    @property
    def unavailabilities(self) -> UnavailabilitiesRepository:
        """Repositório de indisponibilidades."""
        return self._require(self._unavailabilities, "indisponibilidades")

    async def __aenter__(self) -> Self:
        await super().__aenter__()
        session = self.session
        self._clients = ClientsRepository(session)
        self._establishments = EstablishmentsRepository(session)
        self._memberships = MembershipsRepository(session)
        self._operating_hours = OperatingHoursRepository(session)
        self._schedulings = SchedulingsRepository(session)
        self._services = ServicesRepository(session)
        self._unavailabilities = UnavailabilitiesRepository(session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:

        await super().__aexit__(exc_type, exc_val, exc_tb)
        self._clients = None
        self._establishments = None
        self._memberships = None
        self._operating_hours = None
        self._schedulings = None
        self._services = None
        self._unavailabilities = None

    def _require[T](self, repository: T | None, name: str) -> T:
        if repository is None:
            raise RuntimeError(f"Repositório de {name} não inicializado.")
        return repository
