import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.pagination.params import PageParams
from app.modules.establishments.adapters.db.models import (
    Establishment as EstablishmentModel,
)
from app.modules.establishments.adapters.db.repository import (
    EstablishmentsRepository,
)
from app.modules.establishments.application.dtos.filters import EstablishmentFilters
from app.modules.establishments.domain.entities import Establishment
from app.modules.establishments.domain.enums import DocumentType


@pytest.fixture
def session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repo(session: AsyncMock) -> EstablishmentsRepository:
    return EstablishmentsRepository(session=session)


@pytest.fixture
def model_row() -> EstablishmentModel:
    now = datetime.now(UTC)
    return EstablishmentModel(
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
        deleted_at=None,
        created_at=now,
        updated_at=now,
    )


async def test_get_by_id_or_none_returns_entity(repo, session, model_row):
    session.get.return_value = model_row

    result = await repo.get_by_id_or_none(model_row.id)

    assert isinstance(result, Establishment)
    assert result.id == model_row.id
    assert result.document == model_row.document


async def test_get_by_id_or_none_ignores_soft_deleted(repo, session, model_row):
    model_row.deleted_at = datetime.now(UTC)
    session.get.return_value = model_row

    result = await repo.get_by_id_or_none(model_row.id)

    assert result is None


async def test_get_by_id_raises_not_found(repo, session):
    session.get.return_value = None

    with pytest.raises(NotFoundError):
        await repo.get_by_id(uuid.uuid7())


async def test_get_by_cnpj_or_none_returns_entity(repo, session, model_row):
    result_mock = MagicMock()
    result_mock.scalars.return_value.one_or_none.return_value = model_row
    session.execute.return_value = result_mock

    result = await repo.get_by_cnpj_or_none(model_row.document)

    assert isinstance(result, Establishment)
    assert result.document == model_row.document


async def test_get_by_cnpj_or_none_returns_none_when_not_found(repo, session):
    result_mock = MagicMock()
    result_mock.scalars.return_value.one_or_none.return_value = None
    session.execute.return_value = result_mock

    result = await repo.get_by_cnpj_or_none("00000000000000")

    assert result is None


async def test_get_by_cnpj_raises_not_found(repo, session):
    result_mock = MagicMock()
    result_mock.scalars.return_value.one_or_none.return_value = None
    session.execute.return_value = result_mock

    with pytest.raises(NotFoundError):
        await repo.get_by_cnpj("00000000000000")


async def test_list_all_applies_filters(repo, session):
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = []
    session.execute.return_value = result_mock

    await repo.list_all(
        EstablishmentFilters(
            name="Clínica",
            document="11222333000181",
            timezone="America/Sao_Paulo",
        )
    )

    session.execute.assert_awaited_once()


async def test_paginate_returns_page(repo, session, model_row):
    session.scalar = AsyncMock(return_value=1)

    rows_result = MagicMock()
    rows_result.scalars.return_value.all.return_value = [model_row]
    session.execute.return_value = rows_result

    page = await repo.paginate(PageParams(page=1, page_size=10))

    assert page.total == 1
    assert page.items[0].id == model_row.id
