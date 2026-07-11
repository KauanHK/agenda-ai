import uuid
from typing import Self
from unittest.mock import AsyncMock

import pytest

from app.modules.memberships.application.ports.repositories import (
    MembershipsRepositoryProtocol,
)
from app.modules.users.application.ports.repositories import UsersRepositoryProtocol


class FakeAuthUnitOfWork:
    """Fake de unit of work de autenticação para testes de use cases."""

    def __init__(self, users_repo: AsyncMock, memberships_repo: AsyncMock) -> None:
        self.users = users_repo
        self.memberships = memberships_repo

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        return None


@pytest.fixture
def establishment_id() -> uuid.UUID:
    return uuid.uuid7()


@pytest.fixture
def mock_users_repo() -> AsyncMock:
    return AsyncMock(spec=UsersRepositoryProtocol)


@pytest.fixture
def mock_memberships_repo() -> AsyncMock:
    return AsyncMock(spec=MembershipsRepositoryProtocol)


@pytest.fixture
def uow(mock_users_repo: AsyncMock, mock_memberships_repo: AsyncMock) -> FakeAuthUnitOfWork:
    return FakeAuthUnitOfWork(mock_users_repo, mock_memberships_repo)
