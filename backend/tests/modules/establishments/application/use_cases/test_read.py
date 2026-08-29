import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.core.actors.user import Membership, UserActor
from app.core.exceptions import NotFoundError
from app.core.roles import UserRole
from app.modules.establishments.application.use_cases.read import EstablishmentsReader


@pytest.fixture
def global_admin() -> UserActor:
    return UserActor(user_id=uuid.uuid7(), is_global_admin=True, memberships=())


def make_member(establishment_id: uuid.UUID) -> UserActor:
    return UserActor(
        user_id=uuid.uuid7(),
        is_global_admin=False,
        memberships=(
            Membership(establishment_id=establishment_id, role=UserRole.MEMBER),
        ),
    )


async def test_get_by_id_returns_entity_for_global_admin(
    uow, establishments_repo, establishment, global_admin
):
    result = await EstablishmentsReader(uow).get_by_id(establishment.id, global_admin)

    assert result == establishment
    establishments_repo.get_by_id.assert_awaited_once_with(establishment.id)


async def test_get_by_id_returns_entity_for_member(uow, establishment):
    actor = make_member(establishment.id)

    result = await EstablishmentsReader(uow).get_by_id(establishment.id, actor)

    assert result == establishment


async def test_get_by_id_checks_membership_for_non_member(uow, establishment):
    actor = UserActor(user_id=uuid.uuid7(), is_global_admin=False, memberships=())

    with patch(
        "app.modules.establishments.application.use_cases.read.MembershipRepository"
    ) as repo_cls:
        memberships_repo = AsyncMock()
        memberships_repo.get_by_user_and_establishment_or_none.return_value = None
        repo_cls.return_value = memberships_repo

        with pytest.raises(NotFoundError, match="não encontrado"):
            await EstablishmentsReader(uow).get_by_id(establishment.id, actor)

        memberships_repo.get_by_user_and_establishment_or_none.assert_awaited_once_with(
            user_id=actor.user_id,
            establishment_id=establishment.id,
        )


async def test_get_by_id_allows_non_member_with_membership_row(uow, establishment):
    actor = UserActor(user_id=uuid.uuid7(), is_global_admin=False, memberships=())

    with patch(
        "app.modules.establishments.application.use_cases.read.MembershipRepository"
    ) as repo_cls:
        memberships_repo = AsyncMock()
        memberships_repo.get_by_user_and_establishment_or_none.return_value = object()
        repo_cls.return_value = memberships_repo

        result = await EstablishmentsReader(uow).get_by_id(establishment.id, actor)

    assert result == establishment


async def test_get_by_id_propagates_not_found(uow, establishments_repo, global_admin):
    establishments_repo.get_by_id.side_effect = NotFoundError("Establishment not found")

    with pytest.raises(NotFoundError):
        await EstablishmentsReader(uow).get_by_id(uuid.uuid7(), global_admin)
