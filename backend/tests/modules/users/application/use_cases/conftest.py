import uuid
from datetime import UTC, datetime
from typing import Self
from unittest.mock import AsyncMock

import pytest

from app.core.actors.user import UserActor
from app.modules.users.application.ports.repositories import UsersRepositoryProtocol
from app.modules.users.domain.entities import User, UserExpanded


class FakeUsersUnitOfWork:
    """Fake de unit of work de usuários para testes de use cases."""

    def __init__(self, repo: AsyncMock) -> None:
        self.users = repo

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        return None


def make_user(is_active: bool = True) -> User:
    return User(
        id=uuid.uuid7(),
        name="Usuario Teste",
        email="usuario@email.com",
        phone=None,
        password_hash="hashed",
        is_global_admin=False,
        is_active=is_active,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def make_user_expanded() -> UserExpanded:
    return UserExpanded(
        id=uuid.uuid7(),
        name="Usuario Teste",
        email="usuario@email.com",
        phone=None,
        is_active=True,
        is_global_admin=False,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        memberships=[],
    )


def make_actor(is_global_admin: bool = False) -> UserActor:
    return UserActor(
        user_id=uuid.uuid7(), is_global_admin=is_global_admin, memberships=()
    )


@pytest.fixture
def user() -> User:
    return make_user()


@pytest.fixture
def mock_repo() -> AsyncMock:
    return AsyncMock(spec=UsersRepositoryProtocol)


@pytest.fixture
def uow(mock_repo: AsyncMock) -> FakeUsersUnitOfWork:
    return FakeUsersUnitOfWork(mock_repo)
