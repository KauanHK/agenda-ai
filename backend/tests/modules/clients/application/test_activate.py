import uuid

import pytest

from app.core.exceptions import ForbiddenError, NotFoundError
from app.modules.clients.application.activate import ClientsActivator
from app.modules.clients.domain.schemas import ClientRead


@pytest.fixture
def activator(mock_uow) -> ClientsActivator:
    return ClientsActivator(uow=mock_uow)


async def test_activate_returns_client_read(activator, admin_user, establishment_id, client_model):
    client_model.is_active = False

    result = await activator.activate(client_model.id, admin_user, establishment_id)

    assert isinstance(result, ClientRead)


async def test_activate_sets_is_active_true(activator, admin_user, establishment_id, client_model):
    client_model.is_active = False

    await activator.activate(client_model.id, admin_user, establishment_id)

    assert client_model.is_active is True


async def test_activate_calls_update(activator, mock_repo, admin_user, establishment_id, client_model):
    await activator.activate(client_model.id, admin_user, establishment_id)

    mock_repo.update.assert_awaited_once_with(client_model)


async def test_deactivate_sets_is_active_false(activator, admin_user, establishment_id, client_model):
    client_model.is_active = True

    await activator.deactivate(client_model.id, admin_user, establishment_id)

    assert client_model.is_active is False


async def test_deactivate_calls_update(activator, mock_repo, admin_user, establishment_id, client_model):
    await activator.deactivate(client_model.id, admin_user, establishment_id)

    mock_repo.update.assert_awaited_once_with(client_model)


async def test_activate_raises_not_found_for_other_tenant(
    activator, admin_user, establishment_id, client_model
):
    client_model.establishment_id = uuid.uuid7()

    with pytest.raises(NotFoundError, match="Acesso negado"):
        await activator.activate(client_model.id, admin_user, establishment_id)


async def test_deactivate_raises_not_found_for_other_tenant(
    activator, admin_user, establishment_id, client_model
):
    client_model.establishment_id = uuid.uuid7()

    with pytest.raises(NotFoundError, match="Acesso negado"):
        await activator.deactivate(client_model.id, admin_user, establishment_id)


async def test_activate_forbidden_for_member(activator, member_user, establishment_id, client_model):
    with pytest.raises(ForbiddenError, match="establishment_admin"):
        await activator.activate(client_model.id, member_user, establishment_id)


async def test_activate_forbidden_for_global_admin(
    activator, global_admin_user, establishment_id, client_model
):
    with pytest.raises(ForbiddenError, match="global_admin"):
        await activator.activate(client_model.id, global_admin_user, establishment_id)


async def test_deactivate_forbidden_for_member(activator, member_user, establishment_id, client_model):
    with pytest.raises(ForbiddenError, match="establishment_admin"):
        await activator.deactivate(client_model.id, member_user, establishment_id)
