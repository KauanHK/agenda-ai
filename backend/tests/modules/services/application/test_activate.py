import uuid

import pytest

from app.core.exceptions import ForbiddenError, NotFoundError
from app.modules.services.application.activate import ServicesActivator
from app.modules.services.domain.schemas import ServiceRead


@pytest.fixture
def activator(mock_uow) -> ServicesActivator:
    return ServicesActivator(uow=mock_uow)


async def test_activate_returns_service_read(activator, admin_user, establishment_id, service_model):
    service_model.is_active = False

    result = await activator.activate(service_model.id, admin_user, establishment_id)

    assert isinstance(result, ServiceRead)


async def test_activate_sets_is_active_true(activator, admin_user, establishment_id, service_model):
    service_model.is_active = False

    await activator.activate(service_model.id, admin_user, establishment_id)

    assert service_model.is_active is True


async def test_activate_calls_update(activator, mock_repo, admin_user, establishment_id, service_model):
    await activator.activate(service_model.id, admin_user, establishment_id)

    mock_repo.update.assert_awaited_once_with(service_model)


async def test_deactivate_sets_is_active_false(activator, admin_user, establishment_id, service_model):
    service_model.is_active = True

    await activator.deactivate(service_model.id, admin_user, establishment_id)

    assert service_model.is_active is False


async def test_deactivate_calls_update(activator, mock_repo, admin_user, establishment_id, service_model):
    await activator.deactivate(service_model.id, admin_user, establishment_id)

    mock_repo.update.assert_awaited_once_with(service_model)


async def test_activate_raises_not_found_for_other_tenant(
    activator, admin_user, establishment_id, service_model
):
    service_model.establishment_id = uuid.uuid7()

    with pytest.raises(NotFoundError, match="Acesso negado"):
        await activator.activate(service_model.id, admin_user, establishment_id)


async def test_deactivate_raises_not_found_for_other_tenant(
    activator, admin_user, establishment_id, service_model
):
    service_model.establishment_id = uuid.uuid7()

    with pytest.raises(NotFoundError, match="Acesso negado"):
        await activator.deactivate(service_model.id, admin_user, establishment_id)


async def test_activate_forbidden_for_member(activator, member_user, establishment_id, service_model):
    with pytest.raises(ForbiddenError, match="establishment_admin"):
        await activator.activate(service_model.id, member_user, establishment_id)


async def test_activate_forbidden_for_global_admin(
    activator, global_admin_user, establishment_id, service_model
):
    with pytest.raises(ForbiddenError, match="global_admin"):
        await activator.activate(service_model.id, global_admin_user, establishment_id)


async def test_deactivate_forbidden_for_member(activator, member_user, establishment_id, service_model):
    with pytest.raises(ForbiddenError, match="establishment_admin"):
        await activator.deactivate(service_model.id, member_user, establishment_id)
