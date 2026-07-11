import uuid

import pytest

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.modules.memberships.application.use_cases.delete import MembershipDeleter
from tests.modules.memberships.application.use_cases.conftest import (
    FakeMembershipsUnitOfWork,
    make_actor,
    make_membership,
)


@pytest.fixture
def deleter(uow: FakeMembershipsUnitOfWork) -> MembershipDeleter:
    return MembershipDeleter(uow=uow)


async def test_delete_removes_membership(
    deleter, mock_memberships_repo, caller_membership
):
    target = make_membership(is_active=True)
    mock_memberships_repo.get_by_user_and_establishment_or_none.side_effect = [
        caller_membership,
        target,
    ]
    mock_memberships_repo.count_admins_in_establishment.return_value = 2
    actor = make_actor(is_global_admin=True)

    await deleter.delete(
        user_id=target.user_id, establishment_id=target.establishment_id, actor=actor
    )

    mock_memberships_repo.delete_by_user_and_establishment.assert_awaited_once_with(
        target.user_id, target.establishment_id
    )


async def test_delete_raises_not_found_when_membership_missing(
    deleter, mock_memberships_repo, caller_membership
):
    mock_memberships_repo.get_by_user_and_establishment_or_none.side_effect = [
        caller_membership,
        None,
    ]
    actor = make_actor(is_global_admin=True)

    with pytest.raises(NotFoundError):
        await deleter.delete(
            user_id=uuid.uuid7(), establishment_id=uuid.uuid7(), actor=actor
        )


async def test_delete_raises_conflict_when_last_admin(
    deleter, mock_memberships_repo, caller_membership
):
    target = make_membership(is_active=True)
    mock_memberships_repo.get_by_user_and_establishment_or_none.side_effect = [
        caller_membership,
        target,
    ]
    mock_memberships_repo.count_admins_in_establishment.return_value = 1
    actor = make_actor(is_global_admin=True)

    with pytest.raises(ConflictError, match="último administrador"):
        await deleter.delete(
            user_id=target.user_id,
            establishment_id=target.establishment_id,
            actor=actor,
        )

    mock_memberships_repo.delete_by_user_and_establishment.assert_not_awaited()


async def test_delete_allows_removing_admin_when_others_remain(
    deleter, mock_memberships_repo, caller_membership
):
    target = make_membership(is_active=True)
    mock_memberships_repo.get_by_user_and_establishment_or_none.side_effect = [
        caller_membership,
        target,
    ]
    mock_memberships_repo.count_admins_in_establishment.return_value = 2
    actor = make_actor(is_global_admin=True)

    await deleter.delete(
        user_id=target.user_id, establishment_id=target.establishment_id, actor=actor
    )

    mock_memberships_repo.delete_by_user_and_establishment.assert_awaited_once()


async def test_delete_raises_forbidden_when_caller_cannot_manage(
    deleter, mock_memberships_repo
):
    mock_memberships_repo.get_by_user_and_establishment_or_none.return_value = None
    actor = make_actor(is_global_admin=False)

    with pytest.raises(ForbiddenError):
        await deleter.delete(
            user_id=uuid.uuid7(), establishment_id=uuid.uuid7(), actor=actor
        )
