import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.core.actors.user import UserActor
from app.core.exceptions import ForbiddenError
from app.db.unit_of_work import UnitOfWork
from app.modules.users.application.activate import UsersActivator
from app.modules.users.domain.model import User
from app.modules.users.domain.schemas import UserRead
from app.modules.users.infra.repository import UsersRepository


def make_user(is_active: bool = False) -> User:
    return User(
        id=uuid.uuid7(),
        name="Usuario Teste",
        email="teste@email.com",
        password_hash="hashed",
        is_global_admin=False,
        is_active=is_active,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def make_actor(is_global_admin: bool = False) -> UserActor:
    return UserActor(
        user_id=uuid.uuid7(), is_global_admin=is_global_admin, memberships=()
    )


@pytest.fixture
def user() -> User:
    return make_user(is_active=False)


@pytest.fixture
def mock_repo(user) -> AsyncMock:
    repo = AsyncMock(spec=UsersRepository)
    repo.get_by_id.return_value = user
    repo.update.return_value = user
    return repo


@pytest.fixture
def mock_uow(mock_repo) -> AsyncMock:
    uow = AsyncMock(spec=UnitOfWork)
    uow.__aenter__.return_value = uow
    uow.__aexit__.return_value = None
    uow.repository.return_value = mock_repo
    return uow


@pytest.fixture
def activator(mock_uow) -> UsersActivator:
    return UsersActivator(uow=mock_uow)


async def test_activate_returns_user_read(activator, user):
    actor = make_actor(is_global_admin=True)

    result = await activator.activate(user.id, actor)

    assert isinstance(result, UserRead)


async def test_activate_sets_is_active_true(activator, user):
    actor = make_actor(is_global_admin=True)

    await activator.activate(user.id, actor)

    assert user.is_active is True


async def test_activate_calls_update(activator, mock_repo, user):
    actor = make_actor(is_global_admin=True)

    await activator.activate(user.id, actor)

    mock_repo.update.assert_awaited_once_with(user)


async def test_deactivate_returns_user_read(activator, user):
    user.is_active = True
    actor = make_actor(is_global_admin=True)

    result = await activator.deactivate(user.id, actor)

    assert isinstance(result, UserRead)


async def test_deactivate_sets_is_active_false(activator, user):
    user.is_active = True
    actor = make_actor(is_global_admin=True)

    await activator.deactivate(user.id, actor)

    assert user.is_active is False


async def test_deactivate_calls_update(activator, mock_repo, user):
    actor = make_actor(is_global_admin=True)

    await activator.deactivate(user.id, actor)

    mock_repo.update.assert_awaited_once_with(user)


async def test_activate_raises_forbidden_for_non_global_admin(activator, user):
    actor = make_actor(is_global_admin=False)

    with pytest.raises(ForbiddenError, match="Acesso negado"):
        await activator.activate(user.id, actor)


async def test_deactivate_raises_forbidden_for_non_global_admin(activator, user):
    actor = make_actor(is_global_admin=False)

    with pytest.raises(ForbiddenError, match="Acesso negado"):
        await activator.deactivate(user.id, actor)
