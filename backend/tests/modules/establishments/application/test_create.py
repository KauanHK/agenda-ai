import uuid
from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError
from app.db.unit_of_work import UnitOfWork
from app.modules.common.domain.enums import DocumentType
from app.modules.establishments.application.create import EstablishmentsCreator
from app.modules.establishments.domain.model import Establishment
from app.modules.establishments.domain.schemas import (
    EstablishmentCreate,
    EstablishmentRead,
)


@pytest.fixture
def establishment_create() -> EstablishmentCreate:
    return EstablishmentCreate(
        name="Clínica Teste",
        document="11222333000181",
        document_type=DocumentType.CNPJ,
        is_active=True,
        timezone="America/Sao_Paulo",
        street="Rua das Flores",
        number="123",
        complement="",
        neighborhood="Centro",
        city="São Paulo",
        state="SP",
        zip_code="01310100",
    )


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
    )


@pytest.fixture
def mock_repo(establishment) -> AsyncMock:

    establishment.id = uuid.uuid7()
    establishment.created_at = datetime.now()
    establishment.updated_at = datetime.now()

    repo = AsyncMock()
    repo.create.return_value = establishment
    return repo


@pytest.fixture
def mock_uow(mock_repo) -> AsyncMock:
    uow = AsyncMock(spec=UnitOfWork)
    uow.__aenter__.return_value = uow
    uow.__aexit__.return_value = False
    uow.repository.return_value = mock_repo
    return uow


@pytest.fixture
def creator(mock_uow) -> EstablishmentsCreator:
    return EstablishmentsCreator(uow=mock_uow)


async def test_create_returns_establishment_read(
    creator, establishment_create, establishment
):
    result = await creator.create(establishment_create)

    assert isinstance(result, EstablishmentRead)
    assert result.name == establishment.name
    assert result.document == establishment.document
    assert result.timezone == establishment.timezone


async def test_create_calls_repository_with_correct_data(
    creator, mock_repo, establishment_create
):
    await creator.create(establishment_create)

    mock_repo.create.assert_awaited_once()
    created_arg = mock_repo.create.call_args[0][0]

    assert created_arg.name == establishment_create.name
    assert created_arg.document == establishment_create.document
    assert created_arg.timezone == establishment_create.timezone


async def test_create_uses_unit_of_work(creator, mock_uow, establishment_create):
    await creator.create(establishment_create)

    mock_uow.__aenter__.assert_awaited_once()
    mock_uow.__aexit__.assert_awaited_once()


async def test_create_instantiates_repository_from_uow(
    creator, mock_uow, establishment_create
):
    await creator.create(establishment_create)

    mock_uow.repository.assert_called_once()


async def test_create_raises_conflict_on_duplicate_cnpj(
    creator, mock_repo, establishment_create
):
    mock_repo.create.side_effect = IntegrityError(None, None, Exception())

    with pytest.raises(ConflictError, match="cpf/cnpj"):
        await creator.create(establishment_create)
