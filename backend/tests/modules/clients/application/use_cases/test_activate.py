import dataclasses
import uuid

import pytest

from app.core.exceptions import ForbiddenError, NotFoundError
from app.modules.clients.application.use_cases.activate import ClientsActivator
from app.modules.clients.domain.entities import Client, UpdateClient


async def test_activate_sends_is_active_true(
    uow, clients_repo, admin_user, establishment_id, client_entity
):
    result = await ClientsActivator(uow).activate(
        client_entity.id, admin_user, establishment_id
    )

    assert isinstance(result, Client)
    sent: UpdateClient = clients_repo.update.call_args.kwargs["update_command"]
    assert sent.is_active is True


async def test_deactivate_sends_is_active_false(
    uow, clients_repo, admin_user, establishment_id, client_entity
):
    await ClientsActivator(uow).deactivate(
        client_entity.id, admin_user, establishment_id
    )

    sent: UpdateClient = clients_repo.update.call_args.kwargs["update_command"]
    assert sent.is_active is False


async def test_activate_raises_not_found_for_other_tenant(
    uow, clients_repo, admin_user, establishment_id, client_entity
):
    clients_repo.get_by_id.return_value = dataclasses.replace(
        client_entity, establishment_id=uuid.uuid7()
    )

    with pytest.raises(NotFoundError, match="Acesso negado"):
        await ClientsActivator(uow).activate(
            client_entity.id, admin_user, establishment_id
        )


async def test_activate_forbidden_for_member(
    uow, member_user, establishment_id, client_entity
):
    with pytest.raises(ForbiddenError, match="establishment_admin"):
        await ClientsActivator(uow).activate(
            client_entity.id, member_user, establishment_id
        )


async def test_activate_forbidden_for_global_admin(
    uow, global_admin_user, establishment_id, client_entity
):
    with pytest.raises(ForbiddenError, match="global_admin"):
        await ClientsActivator(uow).activate(
            client_entity.id, global_admin_user, establishment_id
        )


async def test_deactivate_forbidden_for_member(
    uow, member_user, establishment_id, client_entity
):
    with pytest.raises(ForbiddenError, match="establishment_admin"):
        await ClientsActivator(uow).deactivate(
            client_entity.id, member_user, establishment_id
        )
