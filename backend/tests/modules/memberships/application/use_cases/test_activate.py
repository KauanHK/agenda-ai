import dataclasses

import pytest

from app.core.exceptions import ForbiddenError
from app.core.roles import UserRole
from app.modules.memberships.application.use_cases.activate import (
    MembershipActivator,
)
from app.modules.memberships.domain.entities import (
    MembershipWithUser,
    UpdateMembership,
)
from tests.modules.memberships.application.use_cases.conftest import (
    FakeMembershipsUnitOfWork,
    make_actor,
    make_membership_user,
)


@pytest.fixture
def activator(uow: FakeMembershipsUnitOfWork) -> MembershipActivator:
    return MembershipActivator(uow=uow)


@pytest.fixture
def membership_with_user(membership) -> MembershipWithUser:
    return MembershipWithUser(
        id=membership.id,
        establishment_id=membership.establishment_id,
        role=membership.role,
        is_active=membership.is_active,
        user=make_membership_user(),
    )


async def test_activate_returns_membership_with_user(
    activator, mock_memberships_repo, caller_membership, membership, membership_with_user
):
    mock_memberships_repo.get_by_user_and_establishment_or_none.return_value = (
        caller_membership
    )
    mock_memberships_repo.update_by_user_and_establishment.return_value = (
        membership_with_user
    )
    actor = make_actor(is_global_admin=True)

    result = await activator.activate(
        user_id=membership.user_id,
        establishment_id=membership.establishment_id,
        actor=actor,
    )

    assert isinstance(result, MembershipWithUser)


async def test_activate_calls_update_with_is_active_true(
    activator, mock_memberships_repo, caller_membership, membership, membership_with_user
):
    mock_memberships_repo.get_by_user_and_establishment_or_none.return_value = (
        caller_membership
    )
    mock_memberships_repo.update_by_user_and_establishment.return_value = (
        membership_with_user
    )
    actor = make_actor(is_global_admin=True)

    await activator.activate(
        user_id=membership.user_id,
        establishment_id=membership.establishment_id,
        actor=actor,
    )

    mock_memberships_repo.update_by_user_and_establishment.assert_awaited_once_with(
        membership.user_id,
        membership.establishment_id,
        UpdateMembership(is_active=True),
    )


async def test_deactivate_calls_update_with_is_active_false(
    activator, mock_memberships_repo, caller_membership, membership, membership_with_user
):
    mock_memberships_repo.get_by_user_and_establishment_or_none.return_value = (
        caller_membership
    )
    mock_memberships_repo.update_by_user_and_establishment.return_value = (
        membership_with_user
    )
    actor = make_actor(is_global_admin=True)

    await activator.deactivate(
        user_id=membership.user_id,
        establishment_id=membership.establishment_id,
        actor=actor,
    )

    mock_memberships_repo.update_by_user_and_establishment.assert_awaited_once_with(
        membership.user_id,
        membership.establishment_id,
        UpdateMembership(is_active=False),
    )


async def test_activate_raises_forbidden_when_not_establishment_member(
    activator, mock_memberships_repo, membership
):
    mock_memberships_repo.get_by_user_and_establishment_or_none.return_value = None
    actor = make_actor(is_global_admin=False)

    with pytest.raises(ForbiddenError):
        await activator.activate(
            user_id=membership.user_id,
            establishment_id=membership.establishment_id,
            actor=actor,
        )


async def test_activate_raises_forbidden_when_not_admin_role(
    activator, mock_memberships_repo, membership, caller_membership
):
    caller_membership = dataclasses.replace(caller_membership, role=UserRole.MEMBER)
    mock_memberships_repo.get_by_user_and_establishment_or_none.return_value = (
        caller_membership
    )
    actor = make_actor(is_global_admin=False)

    with pytest.raises(ForbiddenError):
        await activator.activate(
            user_id=membership.user_id,
            establishment_id=membership.establishment_id,
            actor=actor,
        )
