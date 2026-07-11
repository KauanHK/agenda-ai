import uuid
from typing import Self
from unittest.mock import AsyncMock

import pytest

from app.core.actors.user import UserActor
from app.core.roles import UserRole
from app.modules.memberships.application.ports.repositories import (
    MembershipsRepositoryProtocol,
)
from app.modules.memberships.domain.entities import Membership, MembershipUser
from app.modules.users.application.ports.repositories import UsersRepositoryProtocol


class FakeMembershipsUnitOfWork:
    """Fake de unit of work de memberships para testes de use cases."""

    def __init__(self, memberships_repo: AsyncMock, users_repo: AsyncMock) -> None:
        self.memberships = memberships_repo
        self.users = users_repo

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        return None


def make_membership(is_active: bool = True) -> Membership:
    return Membership(
        id=uuid.uuid7(),
        user_id=uuid.uuid7(),
        establishment_id=uuid.uuid7(),
        role=UserRole.ESTABLISHMENT_ADMIN,
        is_active=is_active,
    )


def make_membership_user() -> MembershipUser:
    return MembershipUser(
        id=uuid.uuid7(),
        name="Usuario Teste",
        email="usuario@email.com",
        phone=None,
        is_active=True,
    )


def make_actor(is_global_admin: bool = True) -> UserActor:
    return UserActor(
        user_id=uuid.uuid7(), is_global_admin=is_global_admin, memberships=()
    )


@pytest.fixture
def membership() -> Membership:
    return make_membership(is_active=True)


@pytest.fixture
def caller_membership() -> Membership:
    return make_membership(is_active=True)


@pytest.fixture
def mock_memberships_repo() -> AsyncMock:
    return AsyncMock(spec=MembershipsRepositoryProtocol)


@pytest.fixture
def mock_users_repo() -> AsyncMock:
    return AsyncMock(spec=UsersRepositoryProtocol)


@pytest.fixture
def uow(
    mock_memberships_repo: AsyncMock, mock_users_repo: AsyncMock
) -> FakeMembershipsUnitOfWork:
    return FakeMembershipsUnitOfWork(mock_memberships_repo, mock_users_repo)
