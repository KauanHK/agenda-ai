import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, ForbiddenError
from app.core.roles import UserRole
from app.modules.memberships.application.dtos.commands import (
    InviteExistingMemberCommand,
    InviteNewMemberCommand,
)
from app.modules.memberships.application.use_cases.create import MembershipCreator
from app.modules.memberships.domain.entities import MembershipExpanded
from app.modules.users.domain.entities import User
from tests.modules.memberships.application.use_cases.conftest import (
    FakeMembershipsUnitOfWork,
    make_actor,
)


@pytest.fixture
def creator(uow: FakeMembershipsUnitOfWork) -> MembershipCreator:
    return MembershipCreator(uow=uow)


@pytest.fixture
def establishment_id() -> uuid.UUID:
    return uuid.uuid7()


@pytest.fixture
def created_user() -> User:
    return User(
        id=uuid.uuid7(),
        name="Novo Usuário",
        email="novo@email.com",
        phone=None,
        password_hash="hashed",
        is_global_admin=False,
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


async def test_create_with_existing_user(
    creator, mock_memberships_repo, caller_membership, establishment_id
):
    mock_memberships_repo.get_by_user_and_establishment_or_none.return_value = (
        caller_membership
    )
    expanded = MembershipExpanded(
        role=UserRole.MEMBER,
        is_active=True,
        user=None,
        establishment=None,
    )
    mock_memberships_repo.get_by_user_and_establishment_expanded.return_value = (
        expanded
    )
    actor = make_actor(is_global_admin=True)
    user_id = uuid.uuid7()

    result = await creator.create(
        establishment_id=establishment_id,
        data=InviteExistingMemberCommand(user_id=user_id, role=UserRole.MEMBER),
        actor=actor,
    )

    assert result is expanded
    mock_memberships_repo.create.assert_awaited_once()


async def test_create_with_new_user_creates_user_and_membership(
    creator,
    mock_memberships_repo,
    mock_users_repo,
    caller_membership,
    created_user,
    establishment_id,
):
    mock_memberships_repo.get_by_user_and_establishment_or_none.return_value = (
        caller_membership
    )
    mock_users_repo.get_by_email_or_none.return_value = None
    mock_users_repo.create.return_value = created_user
    expanded = MembershipExpanded(
        role=UserRole.MEMBER, is_active=True, user=None, establishment=None
    )
    mock_memberships_repo.get_by_user_and_establishment_expanded.return_value = (
        expanded
    )
    actor = make_actor(is_global_admin=True)

    await creator.create(
        establishment_id=establishment_id,
        data=InviteNewMemberCommand(
            name="Novo Usuário",
            email="novo@email.com",
            password="senha1234",
            role=UserRole.MEMBER,
        ),
        actor=actor,
    )

    mock_users_repo.create.assert_awaited_once()
    new_membership = mock_memberships_repo.create.call_args[0][0]
    assert new_membership.user_id == created_user.id


async def test_create_raises_conflict_when_email_already_used(
    creator, mock_memberships_repo, mock_users_repo, caller_membership, establishment_id
):
    mock_memberships_repo.get_by_user_and_establishment_or_none.return_value = (
        caller_membership
    )
    mock_users_repo.get_by_email_or_none.return_value = object()
    actor = make_actor(is_global_admin=True)

    with pytest.raises(ConflictError, match="Já existe um usuário"):
        await creator.create(
            establishment_id=establishment_id,
            data=InviteNewMemberCommand(
                name="Novo Usuário",
                email="novo@email.com",
                password="senha1234",
                role=UserRole.MEMBER,
            ),
            actor=actor,
        )


async def test_create_raises_conflict_on_duplicate_membership(
    creator, mock_memberships_repo, caller_membership, establishment_id
):
    mock_memberships_repo.get_by_user_and_establishment_or_none.return_value = (
        caller_membership
    )
    mock_memberships_repo.create.side_effect = IntegrityError(None, None, Exception())
    actor = make_actor(is_global_admin=True)

    with pytest.raises(ConflictError, match="já é membro"):
        await creator.create(
            establishment_id=establishment_id,
            data=InviteExistingMemberCommand(user_id=uuid.uuid7(), role=UserRole.MEMBER),
            actor=actor,
        )


async def test_create_raises_forbidden_when_caller_cannot_manage(
    creator, mock_memberships_repo, establishment_id
):
    mock_memberships_repo.get_by_user_and_establishment_or_none.return_value = None
    actor = make_actor(is_global_admin=False)

    with pytest.raises(ForbiddenError):
        await creator.create(
            establishment_id=establishment_id,
            data=InviteExistingMemberCommand(user_id=uuid.uuid7(), role=UserRole.MEMBER),
            actor=actor,
        )
