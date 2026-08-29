import uuid
from datetime import UTC, date, datetime, time
from decimal import Decimal
from types import TracebackType
from typing import Any, Self
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.actors.customer import CustomerActor
from app.core.roles import UserRole
from app.modules.establishments.domain.entities import Establishment
from app.modules.establishments.domain.enums import DocumentType
from app.modules.memberships.domain.entities import Membership
from app.modules.operating_hours.domain.entities import OperatingHour
from app.modules.schedulings.domain.enums import SchedulingSource, SchedulingStatus
from app.modules.schedulings.domain.model import Scheduling
from app.modules.services.domain.model import Service
from app.modules.unavailabilities.domain.entities import Unavailability

# Segunda-feira. O fuso de referência é America/Sao_Paulo (UTC-3), então 09:00 local
# equivale a 12:00 UTC — é essa conversão que a maioria dos testes verifica.
TARGET_DATE = date(2026, 9, 7)
NOW = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)


def utc(hour: int, minute: int = 0, day: date = TARGET_DATE) -> datetime:
    """Monta um instante UTC no dia de referência."""

    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=UTC)


class FakeBookingUnitOfWork:
    """Fake de `BookingUnitOfWorkProtocol` para testar os use cases isoladamente."""

    def __init__(self, **repositories: Any) -> None:
        self.clients = repositories.get("clients") or AsyncMock()
        self.establishments = repositories.get("establishments") or AsyncMock()
        self.memberships = repositories.get("memberships") or AsyncMock()
        self.operating_hours = repositories.get("operating_hours") or AsyncMock()
        self.schedulings = repositories.get("schedulings") or AsyncMock()
        self.services = repositories.get("services") or AsyncMock()
        self.unavailabilities = repositories.get("unavailabilities") or AsyncMock()
        self.session = repositories.get("session") or AsyncMock()
        self.entered = False
        self.exited = False

    async def __aenter__(self) -> Self:
        self.entered = True
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.exited = True
        return None


def make_service(establishment_id: uuid.UUID, **overrides: Any) -> Service:
    defaults: dict[str, Any] = {
        "id": uuid.uuid7(),
        "establishment_id": establishment_id,
        "name": "Corte de cabelo",
        "description": "Corte masculino",
        "duration_minutes": 60,
        "price": Decimal("50.00"),
        "is_active": True,
        "deleted_at": None,
    }
    return Service(**(defaults | overrides))


def make_scheduling(
    establishment_id: uuid.UUID,
    user_id: uuid.UUID,
    starts_at: datetime,
    ends_at: datetime,
    **overrides: Any,
) -> Scheduling:
    defaults: dict[str, Any] = {
        "id": uuid.uuid7(),
        "establishment_id": establishment_id,
        "user_id": user_id,
        "client_id": uuid.uuid7(),
        "service_id": uuid.uuid7(),
        "status": SchedulingStatus.CONFIRMED,
        "source": SchedulingSource.APP,
        "starts_at": starts_at,
        "ends_at": ends_at,
    }
    return Scheduling(**(defaults | overrides))


def make_operating_hour(
    establishment_id: uuid.UUID,
    weekday: int,
    start: time,
    end: time,
) -> OperatingHour:
    return OperatingHour(
        id=uuid.uuid7(),
        establishment_id=establishment_id,
        weekday=weekday,
        start_time=start,
        end_time=end,
    )


def make_unavailability(
    establishment_id: uuid.UUID,
    starts_at: datetime,
    ends_at: datetime,
) -> Unavailability:
    now = datetime.now(UTC)
    return Unavailability(
        id=uuid.uuid7(),
        establishment_id=establishment_id,
        starts_at=starts_at,
        ends_at=ends_at,
        reason="Feriado",
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def establishment_id() -> uuid.UUID:
    return uuid.uuid7()


@pytest.fixture
def client_id() -> uuid.UUID:
    return uuid.uuid7()


@pytest.fixture
def professional_id() -> uuid.UUID:
    return uuid.uuid7()


@pytest.fixture
def actor(establishment_id: uuid.UUID, client_id: uuid.UUID) -> CustomerActor:
    return CustomerActor(
        establishment_id=establishment_id,
        client_id=client_id,
        phone="+5547999998888",
    )


@pytest.fixture
def establishment(establishment_id: uuid.UUID) -> Establishment:
    now = datetime.now(UTC)
    return Establishment(
        id=establishment_id,
        name="Barbearia Teste",
        document="12345678000199",
        document_type=DocumentType.CNPJ,
        timezone="America/Sao_Paulo",
        street="Rua Teste",
        number="100",
        complement=None,
        neighborhood="Centro",
        city="Joinville",
        state="SC",
        zip_code="89200000",
        is_active=True,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def service(establishment_id: uuid.UUID) -> Service:
    return make_service(establishment_id)


@pytest.fixture
def establishments_repo(establishment: Establishment) -> AsyncMock:
    repo = AsyncMock()
    repo.get_by_id.return_value = establishment
    repo.get_by_id_or_none.return_value = establishment
    return repo


@pytest.fixture
def memberships_repo(
    establishment_id: uuid.UUID,
    professional_id: uuid.UUID,
) -> AsyncMock:
    repo = AsyncMock()
    repo.list_all_by_establishment.return_value = [
        Membership(
            id=uuid.uuid7(),
            user_id=professional_id,
            establishment_id=establishment_id,
            role=UserRole.MEMBER,
            is_active=True,
        )
    ]
    return repo


@pytest.fixture
def operating_hours_repo(establishment_id: uuid.UUID) -> AsyncMock:
    """Segunda-feira em dois turnos: 09:00-12:00 e 14:00-18:00."""

    repo = AsyncMock()
    repo.list_by_establishment.return_value = [
        make_operating_hour(establishment_id, 0, time(9, 0), time(12, 0)),
        make_operating_hour(establishment_id, 0, time(14, 0), time(18, 0)),
    ]
    return repo


@pytest.fixture
def schedulings_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.list_overlapping.return_value = []
    repo.has_client_overlap.return_value = False
    return repo


@pytest.fixture
def unavailabilities_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.list_overlapping.return_value = []
    return repo


@pytest.fixture
def services_repo(service: Service) -> AsyncMock:
    repo = AsyncMock()
    repo.get_by_id_or_none.return_value = service
    repo.list.return_value = [service]
    return repo


@pytest.fixture
def uow(
    establishments_repo: AsyncMock,
    memberships_repo: AsyncMock,
    operating_hours_repo: AsyncMock,
    schedulings_repo: AsyncMock,
    services_repo: AsyncMock,
    unavailabilities_repo: AsyncMock,
) -> FakeBookingUnitOfWork:
    return FakeBookingUnitOfWork(
        establishments=establishments_repo,
        memberships=memberships_repo,
        operating_hours=operating_hours_repo,
        schedulings=schedulings_repo,
        services=services_repo,
        unavailabilities=unavailabilities_repo,
        session=MagicMock(add=MagicMock(), flush=AsyncMock(), execute=AsyncMock()),
    )
