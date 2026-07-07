import uuid
from unittest.mock import AsyncMock

import pytest

import app.db.models  # noqa: F401 — registers all SQLAlchemy models (resolves relationships)
from app.core.actors.user import UserActor
from app.core.exceptions import ForbiddenError
from app.db.unit_of_work import UnitOfWork
from app.modules.memberships.application.activate import MembershipActivator
from app.modules.memberships.domain.model import Membership
from app.modules.memberships.domain.schemas import MembershipRead
from app.modules.memberships.infra.repository import MembershipRepository
from app.modules.users.domain.enums import UserRole
from app.modules.users.domain.model import User


def make_user() -> User:
    user = User(
        id=uuid.uuid7(),
        name="Test User",
        email="test@example.com",
        password_hash="hashed",
        is_active=True,
    )
    return user


def make_membership(is_active: bool = True) -> Membership:
    user = make_user()
    m = Membership(
        id=uuid.uuid7(),
        user_id=user.id,
        establishment_id=uuid.uuid7(),
        role=UserRole.ESTABLISHMENT_ADMIN,
        is_active=is_active,
    )
    m.user = user
    return m


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
def mock_repo(membership, caller_membership) -> AsyncMock:
    repo = AsyncMock(spec=MembershipRepository)
    repo.get_by_user_and_establishment_or_none.return_value = caller_membership
    repo.get_by_user_and_establishment.return_value = membership
    repo.update.return_value = membership
    return repo


@pytest.fixture
def mock_uow(mock_repo) -> AsyncMock:
    uow = AsyncMock(spec=UnitOfWork)
    uow.__aenter__.return_value = uow
    uow.__aexit__.return_value = None
    uow.repository.return_value = mock_repo
    return uow


@pytest.fixture
def activator(mock_uow) -> MembershipActivator:
    return MembershipActivator(uow=mock_uow)


async def test_activate_returns_membership_read(activator, membership):
    actor = make_actor(is_global_admin=True)

    result = await activator.activate(
        user_id=membership.user_id,
        establishment_id=membership.establishment_id,
        actor=actor,
    )

    assert isinstance(result, MembershipRead)


async def test_activate_sets_is_active_true(activator, membership):
    membership.is_active = False
    actor = make_actor(is_global_admin=True)

    await activator.activate(
        user_id=membership.user_id,
        establishment_id=membership.establishment_id,
        actor=actor,
    )

    assert membership.is_active is True


async def test_activate_calls_repo_update(activator, mock_repo, membership):
    actor = make_actor(is_global_admin=True)

    await activator.activate(
        user_id=membership.user_id,
        establishment_id=membership.establishment_id,
        actor=actor,
    )

    mock_repo.update.assert_awaited_once_with(membership)


async def test_deactivate_returns_membership_read(activator, membership):
    actor = make_actor(is_global_admin=True)

    result = await activator.deactivate(
        user_id=membership.user_id,
        establishment_id=membership.establishment_id,
        actor=actor,
    )

    assert isinstance(result, MembershipRead)


async def test_deactivate_sets_is_active_false(activator, membership):
    membership.is_active = True
    actor = make_actor(is_global_admin=True)

    await activator.deactivate(
        user_id=membership.user_id,
        establishment_id=membership.establishment_id,
        actor=actor,
    )

    assert membership.is_active is False


async def test_deactivate_calls_repo_update(activator, mock_repo, membership):
    actor = make_actor(is_global_admin=True)

    await activator.deactivate(
        user_id=membership.user_id,
        establishment_id=membership.establishment_id,
        actor=actor,
    )

    mock_repo.update.assert_awaited_once_with(membership)


async def test_activate_raises_forbidden_when_not_establishment_member(
    activator, mock_repo, membership
):
    mock_repo.get_by_user_and_establishment_or_none.return_value = None
    actor = make_actor(is_global_admin=False)

    with pytest.raises(ForbiddenError):
        await activator.activate(
            user_id=membership.user_id,
            establishment_id=membership.establishment_id,
            actor=actor,
        )


async def test_activate_raises_forbidden_when_not_admin_role(
    activator, mock_repo, membership, caller_membership
):
    caller_membership.role = UserRole.MEMBER
    actor = make_actor(is_global_admin=False)

    with pytest.raises(ForbiddenError):
        await activator.activate(
            user_id=membership.user_id,
            establishment_id=membership.establishment_id,
            actor=actor,
        )
