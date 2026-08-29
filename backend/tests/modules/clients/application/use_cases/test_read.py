import dataclasses
import uuid

import pytest

from app.core.exceptions import ForbiddenError, NotFoundError
from app.modules.clients.application.use_cases.read import ClientsReader
from app.modules.clients.domain.entities import Client


async def test_get_by_id_returns_entity_for_same_tenant(
    uow, admin_user, establishment_id, client_entity
):
    result = await ClientsReader(uow).get_by_id(
        client_entity.id, admin_user, establishment_id
    )

    assert isinstance(result, Client)
    assert result.id == client_entity.id


async def test_get_by_id_calls_repository(
    uow, clients_repo, admin_user, establishment_id, client_entity
):
    await ClientsReader(uow).get_by_id(client_entity.id, admin_user, establishment_id)

    clients_repo.get_by_id.assert_awaited_once_with(client_entity.id)


async def test_get_by_id_allowed_for_member(
    uow, member_user, establishment_id, client_entity
):
    result = await ClientsReader(uow).get_by_id(
        client_entity.id, member_user, establishment_id
    )

    assert isinstance(result, Client)


async def test_get_by_id_raises_not_found_for_other_tenant(
    uow, clients_repo, admin_user, establishment_id, client_entity
):
    clients_repo.get_by_id.return_value = dataclasses.replace(
        client_entity, establishment_id=uuid.uuid7()
    )

    with pytest.raises(NotFoundError, match="Acesso negado"):
        await ClientsReader(uow).get_by_id(
            client_entity.id, admin_user, establishment_id
        )


async def test_get_by_id_forbidden_for_global_admin(
    uow, global_admin_user, establishment_id, client_entity
):
    with pytest.raises(ForbiddenError, match="global_admin"):
        await ClientsReader(uow).get_by_id(
            client_entity.id, global_admin_user, establishment_id
        )
