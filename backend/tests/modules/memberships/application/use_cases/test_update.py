import uuid

import pytest

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.core.roles import UserRole
from app.modules.memberships.application.dtos.commands import UpdateMembershipCommand
from app.modules.memberships.application.use_cases.update import MembershipUpdater
from app.modules.memberships.domain.entities import MembershipWithUser
from tests.modules.memberships.application.use_cases.conftest import (
    FakeMembershipsUnitOfWork,
    make_actor,
    make_membership,
    make_membership_user,
)


@pytest.fixture
def updater(uow: FakeMembershipsUnitOfWork) -> MembershipUpdater:
    return MembershipUpdater(uow=uow)


async def test_update_changes_role(mock_memberships_repo, updater, caller_membership):
    target = make_membership(is_active=True)
    updated = MembershipWithUser(
        id=target.id,
        establishment_id=target.establishment_id,
        role=UserRole.MEMBER,
        is_active=True,
        user=make_membership_user(),
    )
    mock_memberships_repo.get_by_user_and_establishment_or_none.side_effect = [
        caller_membership,
        target,
    ]
    mock_memberships_repo.update_by_user_and_establishment.return_value = updated
    mock_memberships_repo.count_admins_in_establishment.return_value = 2
    actor = make_actor(is_global_admin=True)

    result = await updater.update(
        user_id=target.user_id,
        establishment_id=target.establishment_id,
        data=UpdateMembershipCommand(role=UserRole.MEMBER),
        actor=actor,
    )

    assert result is updated


async def test_update_raises_not_found_when_missing(
    updater, mock_memberships_repo, caller_membership
):
    mock_memberships_repo.get_by_user_and_establishment_or_none.side_effect = [
        caller_membership,
        None,
    ]
    actor = make_actor(is_global_admin=True)

    with pytest.raises(NotFoundError):
        await updater.update(
            user_id=uuid.uuid7(),
            establishment_id=uuid.uuid7(),
            data=UpdateMembershipCommand(role=UserRole.MEMBER),
            actor=actor,
        )


async def test_update_raises_conflict_when_demoting_last_admin(
    updater, mock_memberships_repo, caller_membership
):
    target = make_membership(is_active=True)
    mock_memberships_repo.get_by_user_and_establishment_or_none.side_effect = [
        caller_membership,
        target,
    ]
    mock_memberships_repo.count_admins_in_establishment.return_value = 1
    actor = make_actor(is_global_admin=True)

    with pytest.raises(ConflictError, match="último administrador"):
        await updater.update(
            user_id=target.user_id,
            establishment_id=target.establishment_id,
            data=UpdateMembershipCommand(role=UserRole.MEMBER),
            actor=actor,
        )

    mock_memberships_repo.update_by_user_and_establishment.assert_not_awaited()


async def test_update_raises_forbidden_when_caller_cannot_manage(
    updater, mock_memberships_repo
):
    mock_memberships_repo.get_by_user_and_establishment_or_none.return_value = None
    actor = make_actor(is_global_admin=False)

    with pytest.raises(ForbiddenError):
        await updater.update(
            user_id=uuid.uuid7(),
            establishment_id=uuid.uuid7(),
            data=UpdateMembershipCommand(role=UserRole.MEMBER),
            actor=actor,
        )
