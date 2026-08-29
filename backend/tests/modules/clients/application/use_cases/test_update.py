import dataclasses
import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.core.types import UNSET
from app.modules.clients.application.dtos.commands import UpdateClientCommand
from app.modules.clients.application.use_cases.update import ClientsUpdater
from app.modules.clients.domain.entities import Client, UpdateClient


async def test_update_returns_entity(uow, admin_user, establishment_id, client_entity):
    result = await ClientsUpdater(uow).update(
        client_entity.id,
        UpdateClientCommand(name="Novo Nome"),
        admin_user,
        establishment_id,
    )

    assert isinstance(result, Client)


async def test_update_only_sends_defined_fields(
    uow, clients_repo, admin_user, establishment_id, client_entity
):
    await ClientsUpdater(uow).update(
        client_entity.id,
        UpdateClientCommand(name="Apenas Nome"),
        admin_user,
        establishment_id,
    )

    sent: UpdateClient = clients_repo.update.call_args.kwargs["update_command"]
    assert sent.name == "Apenas Nome"
    assert sent.phone is UNSET
    assert sent.email is UNSET
    assert sent.is_active is UNSET


async def test_update_calls_get_by_id_and_update(
    uow, clients_repo, admin_user, establishment_id, client_entity
):
    await ClientsUpdater(uow).update(
        client_entity.id, UpdateClientCommand(name="X"), admin_user, establishment_id
    )

    clients_repo.get_by_id.assert_awaited_once_with(client_entity.id)
    assert clients_repo.update.call_args.kwargs["id_"] == client_entity.id


async def test_update_can_change_is_active(
    uow, clients_repo, admin_user, establishment_id, client_entity
):
    await ClientsUpdater(uow).update(
        client_entity.id,
        UpdateClientCommand(is_active=False),
        admin_user,
        establishment_id,
    )

    sent: UpdateClient = clients_repo.update.call_args.kwargs["update_command"]
    assert sent.is_active is False


async def test_update_raises_not_found_for_other_tenant(
    uow, clients_repo, admin_user, establishment_id, client_entity
):
    clients_repo.get_by_id.return_value = dataclasses.replace(
        client_entity, establishment_id=uuid.uuid7()
    )

    with pytest.raises(NotFoundError, match="Acesso negado"):
        await ClientsUpdater(uow).update(
            client_entity.id,
            UpdateClientCommand(name="X"),
            admin_user,
            establishment_id,
        )


async def test_update_raises_conflict_on_integrity_error(
    uow, clients_repo, admin_user, establishment_id, client_entity
):
    clients_repo.update.side_effect = IntegrityError(None, None, Exception())

    with pytest.raises(ConflictError, match="Telefone ou e-mail já cadastrado"):
        await ClientsUpdater(uow).update(
            client_entity.id,
            UpdateClientCommand(phone="11900000001"),
            admin_user,
            establishment_id,
        )


async def test_update_forbidden_for_member(
    uow, member_user, establishment_id, client_entity
):
    with pytest.raises(ForbiddenError, match="establishment_admin"):
        await ClientsUpdater(uow).update(
            client_entity.id,
            UpdateClientCommand(name="X"),
            member_user,
            establishment_id,
        )


async def test_update_forbidden_for_global_admin(
    uow, global_admin_user, establishment_id, client_entity
):
    with pytest.raises(ForbiddenError, match="global_admin"):
        await ClientsUpdater(uow).update(
            client_entity.id,
            UpdateClientCommand(name="X"),
            global_admin_user,
            establishment_id,
        )
