import pytest
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, ForbiddenError
from app.modules.clients.application.create import ClientsCreator
from app.modules.clients.domain.model import Client
from app.modules.clients.domain.schemas import ClientCreate, ClientRead
from tests.modules.clients.application.conftest import make_actor


@pytest.fixture
def creator(mock_uow) -> ClientsCreator:
    return ClientsCreator(uow=mock_uow)


@pytest.fixture
def payload() -> ClientCreate:
    return ClientCreate(
        name="Novo Cliente",
        phone="11955554444",
        email="novo@email.com",
    )


async def test_create_returns_client_read(creator, admin_user, establishment_id, payload):
    result = await creator.create(payload, admin_user, establishment_id)

    assert isinstance(result, ClientRead)


async def test_create_calls_repo_with_client_scoped_to_establishment(
    creator, mock_repo, admin_user, establishment_id, payload
):
    await creator.create(payload, admin_user, establishment_id)

    mock_repo.create.assert_awaited_once()
    sent: Client = mock_repo.create.call_args[0][0]
    assert sent.establishment_id == establishment_id
    assert sent.name == payload.name
    assert sent.phone == payload.phone
    assert sent.email == payload.email


async def test_create_accepts_email_none(creator, mock_repo, admin_user, establishment_id):
    payload = ClientCreate(name="Sem Email", phone="11900000000")

    await creator.create(payload, admin_user, establishment_id)

    sent: Client = mock_repo.create.call_args[0][0]
    assert sent.email is None


async def test_create_raises_conflict_on_integrity_error(
    creator, mock_repo, admin_user, establishment_id, payload
):
    mock_repo.create.side_effect = IntegrityError(None, None, Exception())

    with pytest.raises(
        ConflictError,
        match="Telefone ou e-mail já cadastrado",
    ):
        await creator.create(payload, admin_user, establishment_id)


async def test_create_forbidden_for_member(creator, member_user, establishment_id, payload):
    with pytest.raises(ForbiddenError, match="establishment_admin"):
        await creator.create(payload, member_user, establishment_id)


async def test_create_forbidden_for_global_admin(creator, global_admin_user, establishment_id, payload):
    with pytest.raises(ForbiddenError, match="global_admin"):
        await creator.create(payload, global_admin_user, establishment_id)


async def test_create_forbidden_when_not_member_of_establishment(creator, establishment_id, payload):
    actor = make_actor()  # no memberships

    with pytest.raises(ForbiddenError, match="Acesso negado"):
        await creator.create(payload, actor, establishment_id)
