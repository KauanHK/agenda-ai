import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import NotFoundError
from app.db.unit_of_work import UnitOfWork
from app.modules.common.domain.enums import DocumentType
from app.modules.establishments.application.update import EstablishmentsUpdater
from app.modules.establishments.domain.model import Establishment
from app.modules.establishments.domain.schemas import (
    EstablishmentRead,
    EstablishmentUpdate,
)
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
def establishment_update() -> EstablishmentUpdate:
    return EstablishmentUpdate(
        name="Clínica Atualizada",
        document="11222333000181",
        timezone="America/Rio_Branco",
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
def updater(mock_uow) -> EstablishmentsUpdater:
    return EstablishmentsUpdater(uow=mock_uow)


@pytest.mark.asyncio
async def test_update_returns_establishment_read(
    updater, mock_repo, establishment, establishment_update
):
    mock_repo.update.return_value = Establishment(
        id=establishment.id,
        name=establishment_update.name,
        document=establishment_update.document,
        document_type=establishment.document_type,
        timezone=establishment_update.timezone,
        street=establishment.street,
        number=establishment.number,
        complement=establishment.complement,
        neighborhood=establishment.neighborhood,
        city=establishment.city,
        state=establishment.state,
        zip_code=establishment.zip_code,
        is_active=establishment.is_active,
        created_at=establishment.created_at,
        updated_at=establishment.updated_at,
    )

    result = await updater.update(establishment.id, establishment_update)

    assert isinstance(result, EstablishmentRead)
    assert result.name == establishment_update.name
    assert result.document == establishment_update.document
    assert result.timezone == establishment_update.timezone


async def test_update_calls_get_by_id_and_update(
    updater, mock_repo, establishment, establishment_update
):
    await updater.update(establishment.id, establishment_update)

    mock_repo.get_by_id.assert_called_once_with(establishment.id)
    mock_repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_update_raises_not_found(updater, mock_repo, establishment_update):
    mock_repo.get_by_id.side_effect = NotFoundError("Establishment not found")

    with pytest.raises(NotFoundError):
        await updater.update(uuid.uuid7(), establishment_update)


@pytest.mark.asyncio
async def test_update_partial_data_only_updates_sent_fields(
    updater, mock_repo, establishment
):
    partial_update = EstablishmentUpdate(name="Novo Nome")
    original_document = establishment.document
    original_timezone = establishment.timezone

    await updater.update(establishment.id, partial_update)

    assert establishment.name == "Novo Nome"
    assert establishment.document == original_document
    assert establishment.timezone == original_timezone


@pytest.mark.asyncio
async def test_update_preserves_unmodified_fields(updater, mock_repo, establishment):
    partial_update = EstablishmentUpdate(name="Novo Nome")

    result = await updater.update(establishment.id, partial_update)

    assert result.document == establishment.document
    assert result.timezone == establishment.timezone
