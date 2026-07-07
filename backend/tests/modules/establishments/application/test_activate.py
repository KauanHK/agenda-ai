import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import NotFoundError
from app.db.unit_of_work import UnitOfWork
from app.modules.common.domain.enums import DocumentType
from app.modules.establishments.application.activate import EstablishmentsActivator
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
        is_active=False,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def mock_repo(establishment) -> AsyncMock:
    repo = AsyncMock(spec=EstablishmentsRepository)
    repo.get_by_id.return_value = establishment
    repo.update.return_value = establishment
    return repo


@pytest.fixture
def mock_uow(mock_repo) -> AsyncMock:
    uow = AsyncMock(spec=UnitOfWork)
    uow.__aenter__.return_value = uow
    uow.__aexit__.return_value = None
    uow.repository.return_value = mock_repo
    return uow


@pytest.fixture
def activator(mock_uow) -> EstablishmentsActivator:
    return EstablishmentsActivator(uow=mock_uow)


async def test_activate_returns_establishment_read(activator, establishment):
    result = await activator.activate(establishment.id)
    assert isinstance(result, EstablishmentRead)


async def test_activate_sets_is_active_true(activator, mock_repo, establishment):
    await activator.activate(establishment.id)
    assert establishment.is_active is True


async def test_activate_calls_update(activator, mock_repo, establishment):
    await activator.activate(establishment.id)
    mock_repo.update.assert_awaited_once_with(establishment)


async def test_activate_raises_not_found(activator, mock_repo):
    mock_repo.get_by_id.side_effect = NotFoundError("Establishment not found")

    with pytest.raises(NotFoundError):
        await activator.activate(uuid.uuid7())


async def test_deactivate_returns_establishment_read(activator, establishment):
    establishment.is_active = True
    result = await activator.deactivate(establishment.id)
    assert isinstance(result, EstablishmentRead)


async def test_deactivate_sets_is_active_false(activator, mock_repo, establishment):
    establishment.is_active = True
    await activator.deactivate(establishment.id)
    assert establishment.is_active is False


async def test_deactivate_calls_update(activator, mock_repo, establishment):
    await activator.deactivate(establishment.id)
    mock_repo.update.assert_awaited_once_with(establishment)


async def test_deactivate_raises_not_found(activator, mock_repo):
    mock_repo.get_by_id.side_effect = NotFoundError("Establishment not found")

    with pytest.raises(NotFoundError):
        await activator.deactivate(uuid.uuid7())
