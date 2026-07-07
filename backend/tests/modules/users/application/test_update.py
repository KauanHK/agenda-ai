import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.actors.user import UserActor
from app.core.exceptions import ConflictError, ForbiddenError
from app.db.unit_of_work import UnitOfWork
from app.modules.users.application.update import UsersUpdater
from app.modules.users.domain.model import User
from app.modules.users.domain.schemas import UserRead, UserUpdate
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
        user_id=uuid.uuid7(), is_global_admin=is_global_admin, memberships=()
    )


@pytest.fixture
def user() -> User:
    return make_user()


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
def updater(mock_uow) -> UsersUpdater:
    return UsersUpdater(uow=mock_uow)


async def test_update_returns_user_read(updater, user):
    actor = make_actor(is_global_admin=True)
    data = UserUpdate(name="Nome Atualizado")

    result = await updater.update(user.id, data, actor)

    assert isinstance(result, UserRead)


async def test_update_calls_get_by_id_and_update(updater, mock_repo, user):
    actor = make_actor(is_global_admin=True)
    data = UserUpdate(name="Nome Atualizado")

    await updater.update(user.id, data, actor)

    mock_repo.get_by_id.assert_awaited_once_with(user.id)
    mock_repo.update.assert_awaited_once()


async def test_update_only_updates_sent_fields(updater, user):
    actor = make_actor(is_global_admin=True)
    original_email = user.email
    original_active = user.is_active

    await updater.update(user.id, UserUpdate(name="Novo Nome"), actor)

    assert user.name == "Novo Nome"
    assert user.email == original_email
    assert user.is_active is original_active


async def test_update_raises_forbidden_for_non_global_admin(updater, user):
    actor = make_actor(is_global_admin=False)

    with pytest.raises(ForbiddenError, match="Acesso negado"):
        await updater.update(user.id, UserUpdate(name="Novo Nome"), actor)


async def test_update_raises_conflict_on_integrity_error(updater, mock_repo, user):
    actor = make_actor(is_global_admin=True)
    mock_repo.update.side_effect = IntegrityError(None, None, Exception())

    with pytest.raises(ConflictError, match="E-mail já está em uso"):
        await updater.update(user.id, UserUpdate(name="Novo Nome"), actor)


async def test_update_me_returns_user_read(updater, user):
    actor = UserActor(user_id=user.id, is_global_admin=False, memberships=())

    result = await updater.update_me(UserUpdate(name="Meu Nome"), actor)

    assert isinstance(result, UserRead)


async def test_update_me_uses_actor_user_id(updater, mock_repo, user):
    actor = UserActor(user_id=user.id, is_global_admin=False, memberships=())

    await updater.update_me(UserUpdate(name="Meu Nome"), actor)

    mock_repo.get_by_id.assert_awaited_once_with(user.id)


async def test_update_me_raises_conflict_on_integrity_error(updater, mock_repo, user):
    actor = UserActor(user_id=user.id, is_global_admin=False, memberships=())
    mock_repo.update.side_effect = IntegrityError(None, None, Exception())

    with pytest.raises(ConflictError, match="E-mail já está em uso"):
        await updater.update_me(UserUpdate(email="duplicado@email.com"), actor)
