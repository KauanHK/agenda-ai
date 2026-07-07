import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.modules.clients.application.update import ClientsUpdater
from app.modules.clients.domain.schemas import ClientRead, ClientUpdate


@pytest.fixture
def updater(mock_uow) -> ClientsUpdater:
    return ClientsUpdater(uow=mock_uow)


async def test_update_returns_client_read(updater, admin_user, establishment_id, client_model):
    data = ClientUpdate(name="Novo Nome")

    result = await updater.update(client_model.id, data, admin_user, establishment_id)

    assert isinstance(result, ClientRead)


async def test_update_only_updates_sent_fields(updater, admin_user, establishment_id, client_model):
    original_phone = client_model.phone
    original_email = client_model.email
    original_active = client_model.is_active

    await updater.update(
        client_model.id,
        ClientUpdate(name="Apenas Nome"),
        admin_user,
        establishment_id,
    )

    assert client_model.name == "Apenas Nome"
    assert client_model.phone == original_phone
    assert client_model.email == original_email
    assert client_model.is_active is original_active


async def test_update_calls_get_by_id_and_update(
    updater, mock_repo, admin_user, establishment_id, client_model
):
    await updater.update(client_model.id, ClientUpdate(name="X"), admin_user, establishment_id)

    mock_repo.get_by_id.assert_awaited_once_with(client_model.id)
    mock_repo.update.assert_awaited_once()


async def test_update_raises_not_found_for_other_tenant(
    updater, admin_user, establishment_id, client_model
):
    client_model.establishment_id = uuid.uuid7()

    with pytest.raises(NotFoundError, match="Acesso negado"):
        await updater.update(
            client_model.id,
            ClientUpdate(name="X"),
            admin_user,
            establishment_id,
        )


async def test_update_raises_conflict_on_integrity_error(
    updater, mock_repo, admin_user, establishment_id, client_model
):
    mock_repo.update.side_effect = IntegrityError(None, None, Exception())

    with pytest.raises(ConflictError, match="Telefone ou e-mail já cadastrado"):
        await updater.update(
            client_model.id,
            ClientUpdate(phone="11900000001"),
            admin_user,
            establishment_id,
        )


async def test_update_forbidden_for_member(updater, member_user, establishment_id, client_model):
    with pytest.raises(ForbiddenError, match="establishment_admin"):
        await updater.update(client_model.id, ClientUpdate(name="X"), member_user, establishment_id)


async def test_update_forbidden_for_global_admin(
    updater, global_admin_user, establishment_id, client_model
):
    with pytest.raises(ForbiddenError, match="global_admin"):
        await updater.update(client_model.id, ClientUpdate(name="X"), global_admin_user, establishment_id)


async def test_update_can_change_is_active(updater, admin_user, establishment_id, client_model):
    client_model.is_active = True

    await updater.update(
        client_model.id,
        ClientUpdate(is_active=False),
        admin_user,
        establishment_id,
    )

    assert client_model.is_active is False
