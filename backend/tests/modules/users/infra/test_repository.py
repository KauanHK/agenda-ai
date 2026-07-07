import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.pagination import PaginationParams
from app.modules.users.domain.enums import UserRole
from app.modules.users.domain.filters import UserFilters
from app.modules.users.domain.model import User
from app.modules.users.infra.repository import UsersRepository


@pytest.fixture
def session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repo(session: AsyncMock) -> UsersRepository:
    return UsersRepository(session=session)


@pytest.fixture
def user() -> User:
    return User(
        id=uuid.uuid7(),
        name="Usuario Teste",
        email="usuario@email.com",
        password_hash="hashed",
        is_active=True,
    )


@pytest.fixture
def pagination() -> PaginationParams:
    return PaginationParams(page=1, size=10)


async def test_get_by_id_or_none_returns_user(repo, session, user):
    session.get.return_value = user

    result = await repo.get_by_id_or_none(user.id)

    session.get.assert_awaited_once_with(User, user.id)
    assert result is user


async def test_get_by_id_or_none_returns_none_when_not_found(repo, session):
    session.get.return_value = None

    result = await repo.get_by_id_or_none(uuid.uuid7())

    assert result is None


async def test_get_by_id_returns_user(repo, session, user):
    session.get.return_value = user

    result = await repo.get_by_id(user.id)

    assert result is user


async def test_get_by_id_raises_not_found(repo, session):
    session.get.return_value = None

    with pytest.raises(NotFoundError, match="User not found"):
        await repo.get_by_id(uuid.uuid7())


async def test_get_by_email_or_none_returns_user(repo, session, user):
    mock_result = MagicMock()
    mock_result.scalars.return_value.one_or_none.return_value = user
    session.execute.return_value = mock_result

    result = await repo.get_by_email_or_none(user.email)

    assert result is user


async def test_get_by_email_or_none_returns_none_when_not_found(repo, session):
    mock_result = MagicMock()
    mock_result.scalars.return_value.one_or_none.return_value = None
    session.execute.return_value = mock_result

    result = await repo.get_by_email_or_none("missing@email.com")

    assert result is None


async def test_list_returns_users(repo, session, user, pagination):
    mock_result = MagicMock()
    mock_result.scalars.return_value.__iter__ = MagicMock(return_value=iter([user]))
    session.execute.return_value = mock_result

    result = await repo.list(pagination=pagination)

    session.execute.assert_awaited_once()
    assert isinstance(result, list)
    assert result[0] is user


async def test_list_with_q_filter(repo, session, pagination):
    mock_result = MagicMock()
    mock_result.scalars.return_value.__iter__ = MagicMock(return_value=iter([]))
    session.execute.return_value = mock_result

    filters = UserFilters(q="usuario")
    await repo.list(pagination=pagination, filters=filters)

    session.execute.assert_awaited_once()


async def test_list_with_all_filters(repo, session, pagination):
    mock_result = MagicMock()
    mock_result.scalars.return_value.__iter__ = MagicMock(return_value=iter([]))
    session.execute.return_value = mock_result

    filters = UserFilters(
        q="usuario",
        role=UserRole.MEMBER,
        is_active=True,
        establishment_id=str(uuid.uuid7()),
    )
    await repo.list(pagination=pagination, filters=filters)

    session.execute.assert_awaited_once()


async def test_list_respects_pagination(repo, session):
    mock_result = MagicMock()
    mock_result.scalars.return_value.__iter__ = MagicMock(return_value=iter([]))
    session.execute.return_value = mock_result

    await repo.list(pagination=PaginationParams(page=2, size=5))

    session.execute.assert_awaited_once()


async def test_count_returns_total(repo, session):
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = 7
    session.execute.return_value = mock_result

    result = await repo.count()

    assert result == 7


async def test_count_with_filters(repo, session):
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = 2
    session.execute.return_value = mock_result

    filters = UserFilters(role=UserRole.ESTABLISHMENT_ADMIN)
    result = await repo.count(filters=filters)

    assert result == 2


async def test_count_returns_zero_when_empty(repo, session):
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = 0
    session.execute.return_value = mock_result

    result = await repo.count()

    assert result == 0


async def test_update_returns_merged_user(repo, session, user):
    session.merge.return_value = user

    result = await repo.update(user)

    session.merge.assert_awaited_once_with(user)
    assert result is user
