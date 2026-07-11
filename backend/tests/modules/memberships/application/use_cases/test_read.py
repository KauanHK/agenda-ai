import uuid
from dataclasses import replace

import pytest

from app.core.exceptions import ForbiddenError
from app.core.pagination.params import Page, PageParams
from app.modules.memberships.application.use_cases.read import MembershipsReader
from app.modules.memberships.domain.entities import MembershipExpanded
from tests.modules.memberships.application.use_cases.conftest import (
    FakeMembershipsUnitOfWork,
    make_actor,
    make_membership_user,
)


@pytest.fixture
def reader(uow: FakeMembershipsUnitOfWork) -> MembershipsReader:
    return MembershipsReader(uow=uow)


async def test_get_by_user_and_establishment_returns_expanded(
    reader, mock_memberships_repo, caller_membership
):
    expanded = MembershipExpanded(
        role=caller_membership.role,
        is_active=True,
        user=make_membership_user(),
        establishment={},
    )
    mock_memberships_repo.get_by_user_and_establishment_or_none.return_value = (
        caller_membership
    )
    mock_memberships_repo.get_by_user_and_establishment_expanded.return_value = (
        expanded
    )
    actor = make_actor(is_global_admin=False)

    result = await reader.get_by_user_and_establishment(
        user_id=caller_membership.user_id,
        establishment_id=caller_membership.establishment_id,
        actor=actor,
    )

    assert result is expanded


async def test_get_by_user_and_establishment_raises_forbidden_for_outsider(
    reader, mock_memberships_repo
):
    mock_memberships_repo.get_by_user_and_establishment_or_none.return_value = None
    actor = make_actor(is_global_admin=False)

    with pytest.raises(ForbiddenError):
        await reader.get_by_user_and_establishment(
            user_id=uuid.uuid7(), establishment_id=uuid.uuid7(), actor=actor
        )


async def test_paginate_returns_page(reader, mock_memberships_repo):
    mock_memberships_repo.list_by_establishment.return_value = []
    mock_memberships_repo.count_by_establishment.return_value = 0
    actor = make_actor(is_global_admin=True)

    result = await reader.paginate(
        establishment_id=uuid.uuid7(),
        actor=actor,
        page_params=PageParams(page=1, page_size=10),
    )

    assert isinstance(result, Page)
    assert result.total == 0


async def test_list_by_user_raises_forbidden_for_other_user(reader):
    actor = make_actor(is_global_admin=False)

    with pytest.raises(ForbiddenError):
        await reader.list_by_user(user_id=uuid.uuid7(), actor=actor)


async def test_list_by_user_allowed_for_self(reader, mock_memberships_repo):
    mock_memberships_repo.list_by_user.return_value = []
    user_id = uuid.uuid7()
    actor = make_actor(is_global_admin=False)
    actor = replace(actor, user_id=user_id)

    result = await reader.list_by_user(user_id=user_id, actor=actor)

    assert result == []
