import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import NotFoundError
from app.db.unit_of_work import UnitOfWork
from app.modules.common.domain.enums import DocumentType
from app.modules.establishments.application.delete import EstablishmentsDeleter
from app.modules.establishments.domain.model import Establishment
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
def mock_repo(establishment) -> AsyncMock:
    repo = AsyncMock(spec=EstablishmentsRepository)
    repo.get_by_id.return_value = establishment
    return repo


@pytest.fixture
def mock_uow(mock_repo) -> AsyncMock:
    uow = AsyncMock(spec=UnitOfWork)
    uow.__aenter__.return_value = uow
    uow.__aexit__.return_value = None
    uow.repository.return_value = mock_repo
    return uow


@pytest.fixture
def deleter(mock_uow) -> EstablishmentsDeleter:
    return EstablishmentsDeleter(uow=mock_uow)


async def test_delete_marks_establishment_as_deleted(deleter, mock_repo, establishment):
    await deleter.delete(establishment.id)

    mock_repo.get_by_id.assert_called_once_with(establishment.id)
    mock_repo.update.assert_called_once_with(establishment)
    assert establishment.deleted_at is not None


async def test_delete_returns_none(deleter, establishment):
    result = await deleter.delete(establishment.id)
    assert result is None


async def test_delete_raises_not_found(deleter, mock_repo):
    mock_repo.get_by_id.side_effect = NotFoundError("Establishment not found")

    with pytest.raises(NotFoundError):
        await deleter.delete(uuid.uuid7())
