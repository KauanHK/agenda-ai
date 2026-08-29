import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.pagination.params import PageParams
from app.modules.clients.adapters.db.models import Client as ClientModel
from app.modules.clients.adapters.db.repository import ClientsRepository
from app.modules.clients.application.dtos.filters import ClientFilters
from app.modules.clients.domain.entities import Client


@pytest.fixture
def session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repo(session: AsyncMock) -> ClientsRepository:
    return ClientsRepository(session=session)


@pytest.fixture
def model_row() -> ClientModel:
    now = datetime.now(UTC)
    return ClientModel(
        id=uuid.uuid7(),
        establishment_id=uuid.uuid7(),
        name="Cliente Teste",
        phone="11988887777",
        email="cliente@email.com",
        is_active=True,
        deleted_at=None,
        created_at=now,
        updated_at=now,
    )


async def test_get_by_id_or_none_returns_entity(repo, session, model_row):
    session.get.return_value = model_row

    result = await repo.get_by_id_or_none(model_row.id)

    assert isinstance(result, Client)
    assert result.id == model_row.id
    assert result.phone == model_row.phone


async def test_get_by_id_or_none_ignores_soft_deleted(repo, session, model_row):
    model_row.deleted_at = datetime.now(UTC)
    session.get.return_value = model_row

    result = await repo.get_by_id_or_none(model_row.id)

    assert result is None


async def test_get_by_id_raises_not_found(repo, session):
    session.get.return_value = None

    with pytest.raises(NotFoundError):
        await repo.get_by_id(uuid.uuid7())


async def test_list_all_applies_filters(repo, session):
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = []
    session.execute.return_value = result_mock

    await repo.list_all(
        ClientFilters(
            q="cli",
            is_active=True,
            establishment_id=str(uuid.uuid7()),
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
