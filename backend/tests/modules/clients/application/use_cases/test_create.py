import pytest
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, ForbiddenError
from app.modules.clients.application.dtos.commands import CreateClientCommand
from app.modules.clients.application.use_cases.create import ClientsCreator
from app.modules.clients.domain.entities import NewClient
from tests.modules.clients.application.use_cases.conftest import make_actor


@pytest.fixture
def payload() -> CreateClientCommand:
    return CreateClientCommand(
        name="Novo Cliente",
        phone="11955554444",
        email="novo@email.com",
    )


async def test_create_returns_entity(uow, admin_user, establishment_id, payload):
    result = await ClientsCreator(uow).create(payload, admin_user, establishment_id)

    assert result.establishment_id == establishment_id


async def test_create_scopes_command_to_establishment(
    uow, clients_repo, admin_user, establishment_id, payload
):
    await ClientsCreator(uow).create(payload, admin_user, establishment_id)

    clients_repo.create.assert_awaited_once()
    sent: NewClient = clients_repo.create.call_args.kwargs["create_command"]
    assert isinstance(sent, NewClient)
    assert sent.establishment_id == establishment_id
    assert sent.name == payload.name
    assert sent.phone == payload.phone
    assert sent.email == payload.email


async def test_create_accepts_email_none(
    uow, clients_repo, admin_user, establishment_id
):
    await ClientsCreator(uow).create(
        CreateClientCommand(name="Sem Email", phone="11900000000"),
        admin_user,
        establishment_id,
    )

    sent: NewClient = clients_repo.create.call_args.kwargs["create_command"]
    assert sent.email is None


async def test_create_raises_conflict_on_integrity_error(
    uow, clients_repo, admin_user, establishment_id, payload
):
    clients_repo.create.side_effect = IntegrityError(None, None, Exception())

    with pytest.raises(ConflictError, match="Telefone ou e-mail já cadastrado"):
        await ClientsCreator(uow).create(payload, admin_user, establishment_id)


async def test_create_forbidden_for_member(
    uow, member_user, establishment_id, payload
):
    with pytest.raises(ForbiddenError, match="establishment_admin"):
        await ClientsCreator(uow).create(payload, member_user, establishment_id)


async def test_create_forbidden_for_global_admin(
    uow, global_admin_user, establishment_id, payload
):
    with pytest.raises(ForbiddenError, match="global_admin"):
        await ClientsCreator(uow).create(payload, global_admin_user, establishment_id)


async def test_create_forbidden_when_not_member(uow, establishment_id, payload):
    with pytest.raises(ForbiddenError, match="Acesso negado"):
        await ClientsCreator(uow).create(payload, make_actor(), establishment_id)
