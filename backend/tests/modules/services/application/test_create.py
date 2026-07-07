from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, ForbiddenError
from app.modules.services.application.create import ServicesCreator
from app.modules.services.domain.model import Service
from app.modules.services.domain.schemas import ServiceCreate, ServiceRead
from tests.modules.services.application.conftest import make_actor


@pytest.fixture
def creator(mock_uow) -> ServicesCreator:
    return ServicesCreator(uow=mock_uow)


@pytest.fixture
def payload() -> ServiceCreate:
    return ServiceCreate(
        name="Novo Serviço",
        description="Descrição do novo serviço",
        duration_minutes=45,
        price=Decimal("75.00"),
    )


async def test_create_returns_service_read(creator, admin_user, establishment_id, payload):
    result = await creator.create(payload, admin_user, establishment_id)

    assert isinstance(result, ServiceRead)


async def test_create_calls_repo_with_service_scoped_to_establishment(
    creator, mock_repo, admin_user, establishment_id, payload
):
    await creator.create(payload, admin_user, establishment_id)

    mock_repo.create.assert_awaited_once()
    sent: Service = mock_repo.create.call_args[0][0]
    assert sent.establishment_id == establishment_id
    assert sent.name == payload.name
    assert sent.description == payload.description
    assert sent.duration_minutes == payload.duration_minutes
    assert sent.price == payload.price


async def test_create_accepts_description_none(creator, mock_repo, admin_user, establishment_id):
    payload = ServiceCreate(
        name="Sem Descrição",
        duration_minutes=30,
        price=Decimal("10.00"),
    )

    await creator.create(payload, admin_user, establishment_id)

    sent: Service = mock_repo.create.call_args[0][0]
    assert sent.description is None


async def test_create_raises_conflict_on_integrity_error(
    creator, mock_repo, admin_user, establishment_id, payload
):
    mock_repo.create.side_effect = IntegrityError(None, None, Exception())

    with pytest.raises(ConflictError, match="Já existe um serviço"):
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
