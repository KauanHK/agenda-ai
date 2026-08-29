import uuid
from datetime import UTC, datetime
from types import TracebackType
from typing import Self
from unittest.mock import AsyncMock

import pytest

from app.core.actors.user import Membership, UserActor
from app.core.roles import UserRole
from app.modules.clients.domain.entities import Client


class FakeClientsUnitOfWork:
    """Fake de `ClientsUnitOfWorkProtocol` para testar os use cases isoladamente."""

    def __init__(self, clients: AsyncMock) -> None:
        self.clients = clients
        self.entered = False
        self.exited = False

    async def __aenter__(self) -> Self:
        self.entered = True
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.exited = True
        return None


def make_actor(
    is_global_admin: bool = False,
    establishment_id: uuid.UUID | None = None,
    role: str | None = None,
) -> UserActor:
    memberships: tuple[Membership, ...] = ()
    if establishment_id is not None and role is not None:
        memberships = (Membership(establishment_id=establishment_id, role=role),)
    return UserActor(
        user_id=uuid.uuid7(), is_global_admin=is_global_admin, memberships=memberships
    )


def make_client(establishment_id: uuid.UUID, **overrides) -> Client:
    now = datetime.now(UTC)
    defaults = dict(  # noqa: C408
        id=uuid.uuid7(),
        establishment_id=establishment_id,
        name="Cliente Teste",
        phone="11988887777",
        email="cliente@email.com",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    defaults.update(overrides)
    return Client(**defaults)


@pytest.fixture
def establishment_id() -> uuid.UUID:
    return uuid.uuid7()


@pytest.fixture
def client_entity(establishment_id) -> Client:
    return make_client(establishment_id)


@pytest.fixture
def clients_repo(client_entity: Client) -> AsyncMock:
    repo = AsyncMock()
    repo.get_by_id.return_value = client_entity
    repo.create.return_value = client_entity
    repo.update.return_value = client_entity
    return repo


@pytest.fixture
def uow(clients_repo: AsyncMock) -> FakeClientsUnitOfWork:
    return FakeClientsUnitOfWork(clients=clients_repo)


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
