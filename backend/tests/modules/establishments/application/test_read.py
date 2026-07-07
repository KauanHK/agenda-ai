import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.core.actors.user import UserActor
from app.core.exceptions import NotFoundError
from app.core.pagination import PaginatedResponse, PaginationParams
from app.db.unit_of_work import UnitOfWork
from app.modules.common.domain.enums import DocumentType
from app.modules.establishments.application.read import EstablishmentsReader
from app.modules.establishments.domain.model import Establishment
from app.modules.establishments.domain.schemas import EstablishmentRead
from app.modules.establishments.infra.repository import EstablishmentsRepository


@pytest.fixture
def establishment() -> Establishment:
    return Establishment(
        id=uuid.uuid7(),
        name="Clínica Teste",
        document="11222333000181",
        document_type=DocumentType.CNPJ,
        timezone="America/Sao_Paulo",
        street="Rua das Flores",
        number="123",
        complement="",
        neighborhood="Centro",
        city="São Paulo",
        state="SP",
        zip_code="01310100",
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def actor() -> UserActor:
    return UserActor(user_id=uuid.uuid7(), is_global_admin=True, memberships=())


@pytest.fixture
def mock_repo(establishment) -> AsyncMock:
    repo = AsyncMock(spec=EstablishmentsRepository)
    repo.get_by_id.return_value = establishment
    repo.list.return_value = [establishment]
    repo.count.return_value = 1
    return repo


@pytest.fixture
def mock_uow(mock_repo) -> AsyncMock:
    uow = AsyncMock(spec=UnitOfWork)
    uow.__aenter__.return_value = uow
    uow.__aexit__.return_value = None
    uow.repository.return_value = mock_repo
    return uow


@pytest.fixture
def reader(mock_uow) -> EstablishmentsReader:
    return EstablishmentsReader(uow=mock_uow)


@pytest.fixture
def pagination() -> PaginationParams:
    return PaginationParams(page=1, size=10)


async def test_get_by_id_returns_establishment_read(reader, actor, establishment):
    result = await reader.get_by_id(establishment.id, actor)

    assert isinstance(result, EstablishmentRead)
    assert result.name == establishment.name
    assert result.document == establishment.document
    assert result.timezone == establishment.timezone


async def test_get_by_id_calls_repository(reader, actor, mock_repo, establishment):
    await reader.get_by_id(establishment.id, actor)
    mock_repo.get_by_id.assert_called_once_with(establishment.id)


async def test_get_by_id_raises_not_found(reader, actor, mock_repo):
    mock_repo.get_by_id.side_effect = NotFoundError("Establishment not found")

    with pytest.raises(NotFoundError):
        await reader.get_by_id(uuid.uuid7(), actor)


async def test_paginate_returns_paginated_response(reader, pagination):
    result = await reader.paginate(pagination)

    assert isinstance(result, PaginatedResponse)
    assert len(result.data) == 1
    assert result.total == 1


async def test_paginate_calls_list_and_count(reader, mock_repo, pagination):
    await reader.paginate(pagination)

    mock_repo.list.assert_called_once()
    mock_repo.count.assert_called_once()


async def test_paginate_returns_empty(reader, mock_repo, pagination):
    mock_repo.list.return_value = []
    mock_repo.count.return_value = 0

    result = await reader.paginate(pagination)

    assert result.data == []
    assert result.total == 0


async def test_paginate_passes_name_filter(reader, mock_repo, pagination):
    await reader.paginate(pagination, name="Clínica")

    filters = mock_repo.list.call_args[1]["filters"]
    assert filters.name == "Clínica"


async def test_paginate_passes_cnpj_filter(reader, mock_repo, pagination):
    await reader.paginate(pagination, cnpj="12345678000190")

    filters = mock_repo.list.call_args[1]["filters"]
    assert filters.document == "12345678000190"


async def test_paginate_passes_timezone_filter(reader, mock_repo, pagination):
    await reader.paginate(pagination, timezone="America/Sao_Paulo")

    filters = mock_repo.list.call_args[1]["filters"]
    assert filters.timezone == "America/Sao_Paulo"


async def test_paginate_passes_all_filters(reader, mock_repo, pagination):
    await reader.paginate(
        pagination,
        name="Clínica",
        cnpj="12345678000190",
        timezone="America/Sao_Paulo",
    )

    filters = mock_repo.list.call_args[1]["filters"]
    assert filters.name == "Clínica"
    assert filters.document == "12345678000190"
    assert filters.timezone == "America/Sao_Paulo"
