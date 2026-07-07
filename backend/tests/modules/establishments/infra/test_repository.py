import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.pagination import PaginationParams
from app.modules.common.domain.enums import DocumentType
from app.modules.establishments.domain.filters import EstablishmentFilters
from app.modules.establishments.domain.model import Establishment
from app.modules.establishments.infra.repository import EstablishmentsRepository


@pytest.fixture
def session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repo(session: AsyncMock) -> EstablishmentsRepository:
    return EstablishmentsRepository(session=session)


@pytest.fixture
def establishment() -> Establishment:
    return Establishment(
        id=uuid.uuid7(),
        name="Clínica Teste",
        document="12345678000195",
        document_type=DocumentType.CNPJ,
        timezone="America/Sao_Paulo",
        is_active=True,
    )


@pytest.fixture
def pagination() -> PaginationParams:
    return PaginationParams(page=1, size=10)


async def test_create_adds_and_returns_establishment(repo, session, establishment):
    result = await repo.create(establishment)

    session.add.assert_called_once_with(establishment)
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once_with(establishment)
    assert result is establishment


async def test_get_by_id_or_none_returns_establishment(repo, session, establishment):
    mock_result = MagicMock()
    mock_result.scalars.return_value.one_or_none.return_value = establishment
    session.execute.return_value = mock_result

    result = await repo.get_by_id_or_none(establishment.id)

    session.execute.assert_awaited_once()
    assert result is establishment


async def test_get_by_id_or_none_returns_none_when_not_found(repo, session):
    mock_result = MagicMock()
    mock_result.scalars.return_value.one_or_none.return_value = None
    session.execute.return_value = mock_result

    result = await repo.get_by_id_or_none(uuid.uuid7())

    assert result is None


async def test_get_by_id_returns_establishment(repo, session, establishment):
    mock_result = MagicMock()
    mock_result.scalars.return_value.one_or_none.return_value = establishment
    session.execute.return_value = mock_result

    result = await repo.get_by_id(establishment.id)

    assert result is establishment


async def test_get_by_id_raises_not_found(repo, session):
    mock_result = MagicMock()
    mock_result.scalars.return_value.one_or_none.return_value = None
    session.execute.return_value = mock_result

    with pytest.raises(NotFoundError, match="Establishment not found"):
        await repo.get_by_id(uuid.uuid7())


async def test_get_by_cnpj_or_none_returns_establishment(repo, session, establishment):
    mock_result = MagicMock()
    mock_result.scalars.return_value.one_or_none.return_value = establishment
    session.execute.return_value = mock_result

    result = await repo.get_by_cnpj_or_none(establishment.document)

    assert result is establishment


async def test_get_by_cnpj_or_none_returns_none_when_not_found(repo, session):
    mock_result = MagicMock()
    mock_result.scalars.return_value.one_or_none.return_value = None
    session.execute.return_value = mock_result

    result = await repo.get_by_cnpj_or_none("00000000000000")

    assert result is None


async def test_get_by_cnpj_returns_establishment(repo, session, establishment):
    mock_result = MagicMock()
    mock_result.scalars.return_value.one_or_none.return_value = establishment
    session.execute.return_value = mock_result

    result = await repo.get_by_cnpj(establishment.document)

    assert result is establishment


async def test_get_by_cnpj_raises_not_found(repo, session):
    mock_result = MagicMock()
    mock_result.scalars.return_value.one_or_none.return_value = None
    session.execute.return_value = mock_result

    with pytest.raises(NotFoundError, match="Establishment not found"):
        await repo.get_by_cnpj("00000000000000")


async def test_list_returns_establishments(repo, session, establishment, pagination):
    mock_result = MagicMock()
    mock_result.scalars.return_value.__iter__ = MagicMock(
        return_value=iter([establishment])
    )
    session.execute.return_value = mock_result

    result = await repo.list(pagination=pagination)

    session.execute.assert_awaited_once()
    assert isinstance(result, list)


async def test_list_with_name_filter(repo, session, pagination):
    mock_result = MagicMock()
    mock_result.scalars.return_value.__iter__ = MagicMock(return_value=iter([]))
    session.execute.return_value = mock_result

    filters = EstablishmentFilters(name="Clínica")
    await repo.list(pagination=pagination, filters=filters)

    session.execute.assert_awaited_once()


async def test_list_with_all_filters(repo, session, pagination):
    mock_result = MagicMock()
    mock_result.scalars.return_value.__iter__ = MagicMock(return_value=iter([]))
    session.execute.return_value = mock_result

    filters = EstablishmentFilters(
        name="Clínica",
        document="12345678000195",
        timezone="America/Sao_Paulo",
    )
    await repo.list(pagination=pagination, filters=filters)

    session.execute.assert_awaited_once()


async def test_list_respects_pagination(repo, session, establishment):
    mock_result = MagicMock()
    mock_result.scalars.return_value.__iter__ = MagicMock(
        return_value=iter([establishment])
    )
    session.execute.return_value = mock_result

    pagination = PaginationParams(page=2, size=5)
    await repo.list(pagination=pagination)

    session.execute.assert_awaited_once()


async def test_count_returns_total(repo, session):
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = 42
    session.execute.return_value = mock_result

    result = await repo.count()

    assert result == 42


async def test_count_with_filters(repo, session):
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = 5
    session.execute.return_value = mock_result

    filters = EstablishmentFilters(name="Clínica")
    result = await repo.count(filters=filters)

    assert result == 5


async def test_count_returns_zero_when_empty(repo, session):
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = 0
    session.execute.return_value = mock_result

    result = await repo.count()

    assert result == 0


async def test_update_returns_merged_establishment(repo, session, establishment):
    session.merge.return_value = establishment

    result = await repo.update(establishment)

    session.merge.assert_awaited_once_with(establishment)
    assert result is establishment
