import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.pagination import PaginationParams
from app.modules.services.domain.filters import ServiceFilters
from app.modules.services.domain.model import Service
from app.modules.services.infra.repository import ServicesRepository


@pytest.fixture
def session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repo(session: AsyncMock) -> ServicesRepository:
    return ServicesRepository(session=session)


@pytest.fixture
def service_model() -> Service:
    return Service(
        id=uuid.uuid7(),
        establishment_id=uuid.uuid7(),
        name="Corte de Cabelo",
        description="Corte masculino tradicional",
        duration_minutes=30,
        price=Decimal("50.00"),
        is_active=True,
    )


@pytest.fixture
def pagination() -> PaginationParams:
    return PaginationParams(page=1, size=10)


async def test_get_by_id_or_none_returns_service(repo, session, service_model):
    session.get.return_value = service_model

    result = await repo.get_by_id_or_none(service_model.id)

    session.get.assert_awaited_once_with(Service, service_model.id)
    assert result is service_model


async def test_get_by_id_or_none_returns_none(repo, session):
    session.get.return_value = None

    result = await repo.get_by_id_or_none(uuid.uuid7())

    assert result is None


async def test_get_by_id_returns_service(repo, session, service_model):
    session.get.return_value = service_model

    result = await repo.get_by_id(service_model.id)

    assert result is service_model


async def test_get_by_id_raises_not_found(repo, session):
    session.get.return_value = None

    with pytest.raises(NotFoundError, match="Service not found"):
        await repo.get_by_id(uuid.uuid7())


async def test_create_adds_flushes_and_refreshes(repo, session, service_model):
    result = await repo.create(service_model)

    session.add.assert_called_once_with(service_model)
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once_with(service_model)
    assert result is service_model


async def test_update_merges_and_refreshes(repo, session, service_model):
    session.merge.return_value = service_model

    result = await repo.update(service_model)

    session.merge.assert_awaited_once_with(service_model)
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once_with(service_model)
    assert result is service_model


async def test_list_returns_services(repo, session, service_model, pagination):
    mock_result = MagicMock()
    mock_result.scalars.return_value.__iter__ = MagicMock(
        return_value=iter([service_model])
    )
    session.execute.return_value = mock_result

    result = await repo.list(pagination=pagination)

    session.execute.assert_awaited_once()
    assert isinstance(result, list)
    assert result[0] is service_model


async def test_list_with_q_filter(repo, session, pagination):
    mock_result = MagicMock()
    mock_result.scalars.return_value.__iter__ = MagicMock(return_value=iter([]))
    session.execute.return_value = mock_result

    await repo.list(
        pagination=pagination,
        filters=ServiceFilters(establishment_id=uuid.uuid7(), q="corte"),
    )

    session.execute.assert_awaited_once()


async def test_list_with_all_filters(repo, session, pagination):
    mock_result = MagicMock()
    mock_result.scalars.return_value.__iter__ = MagicMock(return_value=iter([]))
    session.execute.return_value = mock_result

    filters = ServiceFilters(
        q="corte",
        is_active=True,
        establishment_id=uuid.uuid7(),
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

    result = await repo.count(
        filters=ServiceFilters(
            establishment_id=uuid.uuid7(),
            is_active=False,
        )
    )

    assert result == 3


async def test_count_returns_zero(repo, session):
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = 0
    session.execute.return_value = mock_result

    result = await repo.count()

    assert result == 0
