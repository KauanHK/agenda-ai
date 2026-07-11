import dataclasses

import pytest

from app.core.exceptions import ForbiddenError
from app.modules.users.application.use_cases.activate import UsersActivator
from app.modules.users.domain.entities import UpdateUser, User
from tests.modules.users.application.use_cases.conftest import (
    FakeUsersUnitOfWork,
    make_actor,
)


@pytest.fixture
def activator(uow: FakeUsersUnitOfWork) -> UsersActivator:
    return UsersActivator(uow=uow)


async def test_activate_returns_user(activator, mock_repo, user: User):
    mock_repo.get_by_id.return_value = user
    mock_repo.update.return_value = dataclasses.replace(user, is_active=True)
    actor = make_actor(is_global_admin=True)

    result = await activator.activate(user.id, actor)

    assert isinstance(result, User)
    assert result.is_active is True


async def test_activate_calls_update_with_is_active_true(activator, mock_repo, user):
    mock_repo.get_by_id.return_value = user
    mock_repo.update.return_value = user
    actor = make_actor(is_global_admin=True)

    await activator.activate(user.id, actor)

    mock_repo.update.assert_awaited_once_with(
        id_=user.id,
        update_command=UpdateUser(is_active=True),
    )


async def test_deactivate_calls_update_with_is_active_false(activator, mock_repo, user):
    mock_repo.get_by_id.return_value = user
    mock_repo.update.return_value = user
    actor = make_actor(is_global_admin=True)

    await activator.deactivate(user.id, actor)

    mock_repo.update.assert_awaited_once_with(
        id_=user.id,
        update_command=UpdateUser(is_active=False),
    )


async def test_activate_raises_forbidden_for_non_global_admin(
    activator, mock_repo, user
):
    mock_repo.get_by_id.return_value = user
    actor = make_actor(is_global_admin=False)

    with pytest.raises(ForbiddenError, match="Acesso negado"):
        await activator.activate(user.id, actor)

    mock_repo.update.assert_not_awaited()


async def test_deactivate_raises_forbidden_for_non_global_admin(
    activator, mock_repo, user
):
    mock_repo.get_by_id.return_value = user
    actor = make_actor(is_global_admin=False)

    with pytest.raises(ForbiddenError, match="Acesso negado"):
        await activator.deactivate(user.id, actor)

    mock_repo.update.assert_not_awaited()
