import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.core.actors.user import Membership, UserActor
from app.db.unit_of_work import UnitOfWork
from app.modules.clients.domain.model import Client
from app.modules.clients.infra.repository import ClientsRepository
from app.modules.users.domain.enums import UserRole


def make_client(
    establishment_id: uuid.UUID,
    name: str = "Cliente Teste",
    phone: str = "11988887777",
    email: str | None = "cliente@email.com",
    is_active: bool = True,
) -> Client:
    return Client(
        id=uuid.uuid7(),
        establishment_id=establishment_id,
        name=name,
        phone=phone,
        email=email,
        is_active=is_active,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def make_actor(
    is_global_admin: bool = False,
    establishment_id: uuid.UUID | None = None,
    role: str | None = None,
) -> UserActor:
    memberships: tuple[Membership, ...] = ()
    if establishment_id is not None and role is not None:
        memberships = (Membership(establishment_id=establishment_id, role=role),)
    return UserActor(
        user_id=uuid.uuid7(),
        is_global_admin=is_global_admin,
        memberships=memberships,
    )


@pytest.fixture
def establishment_id() -> uuid.UUID:
    return uuid.uuid7()


@pytest.fixture
def client_model(establishment_id) -> Client:
    return make_client(establishment_id=establishment_id)


@pytest.fixture
def mock_repo(client_model) -> AsyncMock:
    repo = AsyncMock(spec=ClientsRepository)
    repo.get_by_id.return_value = client_model
    repo.create.return_value = client_model
    repo.update.return_value = client_model
    repo.list.return_value = [client_model]
    repo.count.return_value = 1
    return repo


@pytest.fixture
def mock_uow(mock_repo) -> AsyncMock:
    uow = AsyncMock(spec=UnitOfWork)
    uow.__aenter__.return_value = uow
    uow.__aexit__.return_value = None
    uow.repository.return_value = mock_repo
    return uow


@pytest.fixture
def admin_user(establishment_id) -> UserActor:
    return make_actor(
        establishment_id=establishment_id, role=UserRole.ESTABLISHMENT_ADMIN
    )


@pytest.fixture
def member_user(establishment_id) -> UserActor:
    return make_actor(establishment_id=establishment_id, role=UserRole.MEMBER)


@pytest.fixture
def global_admin_user() -> UserActor:
    return make_actor(is_global_admin=True)
