import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.pagination import PaginationParams
from app.modules.clients.domain.filters import ClientFilters
from app.modules.clients.domain.model import Client
from app.modules.clients.infra.repository import ClientsRepository


@pytest.fixture
def session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repo(session: AsyncMock) -> ClientsRepository:
    return ClientsRepository(session=session)


@pytest.fixture
def client_model() -> Client:
    return Client(
        id=uuid.uuid7(),
        establishment_id=uuid.uuid7(),
        name="Cliente Teste",
        phone="11988887777",
        email="cliente@email.com",
        is_active=True,
    )


@pytest.fixture
def pagination() -> PaginationParams:
    return PaginationParams(page=1, size=10)


async def test_get_by_id_or_none_returns_client(repo, session, client_model):
    session.get.return_value = client_model

    result = await repo.get_by_id_or_none(client_model.id)

    session.get.assert_awaited_once_with(Client, client_model.id)
    assert result is client_model


async def test_get_by_id_or_none_returns_none(repo, session):
    session.get.return_value = None

    result = await repo.get_by_id_or_none(uuid.uuid7())

    assert result is None


async def test_get_by_id_returns_client(repo, session, client_model):
    session.get.return_value = client_model

    result = await repo.get_by_id(client_model.id)

    assert result is client_model


async def test_get_by_id_raises_not_found(repo, session):
    session.get.return_value = None

    with pytest.raises(NotFoundError, match="Client not found"):
        await repo.get_by_id(uuid.uuid7())


async def test_create_adds_flushes_and_refreshes(repo, session, client_model):
    result = await repo.create(client_model)

    session.add.assert_called_once_with(client_model)
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once_with(client_model)
    assert result is client_model


async def test_update_merges_and_refreshes(repo, session, client_model):
    session.merge.return_value = client_model

    result = await repo.update(client_model)

    session.merge.assert_awaited_once_with(client_model)
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once_with(client_model)
    assert result is client_model


async def test_list_returns_clients(repo, session, client_model, pagination):
    mock_result = MagicMock()
    mock_result.scalars.return_value.__iter__ = MagicMock(
        return_value=iter([client_model])
    )
    session.execute.return_value = mock_result

    result = await repo.list(pagination=pagination)

    session.execute.assert_awaited_once()
    assert isinstance(result, list)
    assert result[0] is client_model


async def test_list_with_q_filter(repo, session, pagination):
    mock_result = MagicMock()
    mock_result.scalars.return_value.__iter__ = MagicMock(return_value=iter([]))
    session.execute.return_value = mock_result

    await repo.list(pagination=pagination, filters=ClientFilters(q="cli"))

    session.execute.assert_awaited_once()


async def test_list_with_all_filters(repo, session, pagination):
    mock_result = MagicMock()
    mock_result.scalars.return_value.__iter__ = MagicMock(return_value=iter([]))
    session.execute.return_value = mock_result

    filters = ClientFilters(
        q="cli",
        is_active=True,
        establishment_id=str(uuid.uuid7()),
    )
    await repo.list(pagination=pagination, filters=filters)

    session.execute.assert_awaited_once()


async def test_list_respects_pagination(repo, session):
    mock_result = MagicMock()
    mock_result.scalars.return_value.__iter__ = MagicMock(return_value=iter([]))
    session.execute.return_value = mock_result

    await repo.list(pagination=PaginationParams(page=3, size=5))

    session.execute.assert_awaited_once()


async def test_count_returns_total(repo, session):
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = 12
    session.execute.return_value = mock_result

    result = await repo.count()

    assert result == 12


async def test_count_with_filters(repo, session):
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = 3
    session.execute.return_value = mock_result

    result = await repo.count(filters=ClientFilters(is_active=False))

    assert result == 3


async def test_count_returns_zero(repo, session):
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = 0
    session.execute.return_value = mock_result

    result = await repo.count()

    assert result == 0
