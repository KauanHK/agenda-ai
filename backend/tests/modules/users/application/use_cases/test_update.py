import pytest
from sqlalchemy.exc import IntegrityError

from app.core.actors.user import UserActor
from app.core.exceptions import ConflictError, ForbiddenError
from app.modules.users.application.dtos.commands import UpdateUserCommand
from app.modules.users.application.use_cases.update import UsersUpdater
from app.modules.users.domain.entities import User
from tests.modules.users.application.use_cases.conftest import (
    FakeUsersUnitOfWork,
    make_actor,
)


@pytest.fixture
def updater(uow: FakeUsersUnitOfWork) -> UsersUpdater:
    return UsersUpdater(uow=uow)


async def test_update_returns_user(updater, mock_repo, user):
    mock_repo.update.return_value = user
    actor = make_actor(is_global_admin=True)

    result = await updater.update(user.id, UpdateUserCommand(name="Novo Nome"), actor)

    assert isinstance(result, User)


async def test_update_calls_get_by_id_and_update(updater, mock_repo, user):
    mock_repo.update.return_value = user
    actor = make_actor(is_global_admin=True)

    await updater.update(user.id, UpdateUserCommand(name="Novo Nome"), actor)

    mock_repo.get_by_id.assert_awaited_once_with(user.id)
    mock_repo.update.assert_awaited_once()


async def test_update_only_sends_defined_fields(updater, mock_repo, user):
    mock_repo.update.return_value = user
    actor = make_actor(is_global_admin=True)

    await updater.update(user.id, UpdateUserCommand(name="Novo Nome"), actor)

    update_command = mock_repo.update.call_args.kwargs["update_command"]
    assert update_command.defined_values() == {"name": "Novo Nome"}


async def test_update_raises_forbidden_for_non_global_admin(updater, mock_repo, user):
    actor = make_actor(is_global_admin=False)

    with pytest.raises(ForbiddenError, match="Acesso negado"):
        await updater.update(user.id, UpdateUserCommand(name="Novo Nome"), actor)

    mock_repo.update.assert_not_awaited()


async def test_update_raises_conflict_on_integrity_error(updater, mock_repo, user):
    mock_repo.update.side_effect = IntegrityError(None, None, Exception())
    actor = make_actor(is_global_admin=True)

    with pytest.raises(ConflictError, match="E-mail já está em uso"):
        await updater.update(user.id, UpdateUserCommand(name="Novo Nome"), actor)


async def test_update_me_returns_user(updater, mock_repo, user):
    mock_repo.update.return_value = user
    actor = UserActor(user_id=user.id, is_global_admin=False, memberships=())

    result = await updater.update_me(UpdateUserCommand(name="Meu Nome"), actor)

    assert isinstance(result, User)


async def test_update_me_uses_actor_user_id(updater, mock_repo, user):
    mock_repo.update.return_value = user
    actor = UserActor(user_id=user.id, is_global_admin=False, memberships=())

    await updater.update_me(UpdateUserCommand(name="Meu Nome"), actor)

    assert mock_repo.update.call_args.kwargs["id_"] == user.id


async def test_update_me_raises_conflict_on_integrity_error(updater, mock_repo, user):
    mock_repo.update.side_effect = IntegrityError(None, None, Exception())
    actor = UserActor(user_id=user.id, is_global_admin=False, memberships=())

    with pytest.raises(ConflictError, match="E-mail já está em uso"):
        await updater.update_me(UpdateUserCommand(email="duplicado@email.com"), actor)
