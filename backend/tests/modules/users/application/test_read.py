import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.core.actors.user import UserActor
from app.core.pagination import PaginatedResponse, PaginationParams
from app.db.unit_of_work import UnitOfWork
from app.modules.users.application.read import UsersReader
from app.modules.users.domain.enums import UserRole
from app.modules.users.domain.filters import UserFilters
from app.modules.users.domain.model import User
from app.modules.users.domain.schemas import UserRead
from app.modules.users.infra.repository import UsersRepository


def make_user() -> User:
    return User(
        id=uuid.uuid7(),
        name="Usuario Teste",
        email="usuario@email.com",
        password_hash="hashed",
        is_global_admin=False,
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def make_actor(is_global_admin: bool = False) -> UserActor:
    return UserActor(
        user_id=uuid.uuid7(),
        is_global_admin=is_global_admin,
        memberships=(),
    )


@pytest.fixture
def user() -> User:
    return make_user()


@pytest.fixture
def mock_repo(user) -> AsyncMock:
    repo = AsyncMock(spec=UsersRepository)
    repo.get_by_id.return_value = user
    repo.get_by_id_expanded.return_value = user
    repo.list.return_value = [user]
    repo.count.return_value = 1
    return repo


@pytest.fixture
def mock_uow(mock_repo) -> AsyncMock:
    uow = AsyncMock(spec=UnitOfWork)
    uow.__aenter__.return_value = uow
    uow.__aexit__.return_value = None
    uow.repository.return_value = mock_repo
    return uow


@pytest.fixture
def reader(mock_uow) -> UsersReader:
    return UsersReader(uow=mock_uow)


@pytest.fixture
def pagination() -> PaginationParams:
    return PaginationParams(page=1, size=10)


async def test_get_by_id_returns_user_read_for_global_admin(reader, user):
    actor = make_actor(is_global_admin=True)

    result = await reader.get_by_id(user.id, actor)

    assert isinstance(result, UserRead)
    assert result.email == user.email


async def test_get_by_id_calls_repository(reader, mock_repo, user):
    actor = make_actor(is_global_admin=True)

    await reader.get_by_id(user.id, actor)

    mock_repo.get_by_id_expanded.assert_awaited_once_with(user.id)


async def test_get_by_id_allowed_for_non_global_admin(reader, user):
    actor = make_actor(is_global_admin=False)

    result = await reader.get_by_id(user.id, actor)

    assert isinstance(result, UserRead)


async def test_paginate_returns_paginated_response(reader, pagination):
    actor = make_actor(is_global_admin=True)

    result = await reader.paginate(pagination, actor)

    assert isinstance(result, PaginatedResponse)
    assert len(result.data) == 1
    assert result.total == 1


async def test_paginate_calls_list_and_count(reader, mock_repo, pagination):
    actor = make_actor(is_global_admin=True)

    await reader.paginate(pagination, actor)

    mock_repo.list.assert_awaited_once()
    mock_repo.count.assert_awaited_once()


async def test_paginate_preserves_incoming_filters(
    reader,
    mock_repo,
    pagination,
):
    actor = make_actor(is_global_admin=True)
    incoming_filters = UserFilters(
        q="teste",
        role=UserRole.MEMBER,
        is_active=True,
    )

    await reader.paginate(pagination, actor, filters=incoming_filters)

    filters = mock_repo.list.call_args[1]["filters"]
    assert filters.q == "teste"
    assert filters.role == UserRole.MEMBER
    assert filters.is_active is True


async def test_paginate_returns_empty(reader, mock_repo, pagination):
    actor = make_actor(is_global_admin=True)
    mock_repo.list.return_value = []
    mock_repo.count.return_value = 0

    result = await reader.paginate(pagination, actor)

    assert result.data == []
    assert result.total == 0
