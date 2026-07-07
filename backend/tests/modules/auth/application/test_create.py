import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.actors.user import Membership, UserActor
from app.core.exceptions import ConflictError, ForbiddenError
from app.db.unit_of_work import UnitOfWork
from app.modules.auth.application.create import UsersCreator
from app.modules.memberships.infra.repository import MembershipRepository
from app.modules.users.domain.enums import UserRole
from app.modules.users.domain.model import User
from app.modules.users.domain.schemas import UserCreate, UserRead
from app.modules.users.infra.repository import UsersRepository


def make_actor(
    is_global_admin: bool = False,
    establishment_id: uuid.UUID | None = None,
    role: UserRole = UserRole.ESTABLISHMENT_ADMIN,
) -> UserActor:
    memberships = ()
    if establishment_id is not None:
        memberships = (Membership(establishment_id=establishment_id, role=role),)
    return UserActor(
        user_id=uuid.uuid7(), is_global_admin=is_global_admin, memberships=memberships
    )


def make_user_create(
    role: UserRole = UserRole.MEMBER,
    establishment_id: uuid.UUID | None = None,
) -> UserCreate:
    return UserCreate(
        name="Novo Usuário",
        email="novo@email.com",
        password="senha1234",
        role=role,
        establishment_id=establishment_id,
    )


@pytest.fixture
def establishment_id() -> uuid.UUID:
    return uuid.uuid7()


@pytest.fixture
def created_user() -> User:
    return User(
        id=uuid.uuid7(),
        name="Novo Usuário",
        email="novo@email.com",
        password_hash="hashed",
        is_global_admin=False,
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def mock_repo(created_user) -> AsyncMock:
    repo = AsyncMock(spec=UsersRepository)
    repo.create.return_value = created_user
    return repo


@pytest.fixture
def mock_membership_repo() -> AsyncMock:
    return AsyncMock(spec=MembershipRepository)


@pytest.fixture
def mock_uow(mock_repo, mock_membership_repo) -> AsyncMock:
    uow = AsyncMock(spec=UnitOfWork)
    uow.__aenter__.return_value = uow
    uow.__aexit__.return_value = None
    uow.repository.side_effect = lambda cls: (
        mock_repo if cls is UsersRepository else mock_membership_repo
    )
    return uow


@pytest.fixture
def creator(mock_uow) -> UsersCreator:
    return UsersCreator(uow=mock_uow)


async def test_global_admin_can_create_member(creator, establishment_id):
    actor = make_actor(is_global_admin=True)
    data = make_user_create(role=UserRole.MEMBER, establishment_id=establishment_id)

    result = await creator.create(data, actor)

    assert isinstance(result, UserRead)


async def test_global_admin_can_create_establishment_admin_with_establishment_id(
    creator, establishment_id
):
    actor = make_actor(is_global_admin=True)
    data = make_user_create(
        role=UserRole.ESTABLISHMENT_ADMIN, establishment_id=establishment_id
    )

    result = await creator.create(data, actor)

    assert isinstance(result, UserRead)


async def test_global_admin_cannot_create_establishment_admin_without_establishment_id(
    creator,
):
    actor = make_actor(is_global_admin=True)
    data = make_user_create(role=UserRole.ESTABLISHMENT_ADMIN, establishment_id=None)

    with pytest.raises(ForbiddenError, match="establishment_id é obrigatório"):
        await creator.create(data, actor)


async def test_global_admin_uses_provided_establishment_id(
    creator, mock_membership_repo, establishment_id
):
    actor = make_actor(is_global_admin=True)
    data = make_user_create(role=UserRole.MEMBER, establishment_id=establishment_id)

    await creator.create(data, actor)

    membership_arg = mock_membership_repo.add.call_args.kwargs["membership"]
    assert membership_arg.establishment_id == establishment_id


async def test_establishment_admin_can_create_member(
    creator, mock_repo, establishment_id
):
    actor = make_actor(
        establishment_id=establishment_id, role=UserRole.ESTABLISHMENT_ADMIN
    )
    data = make_user_create(role=UserRole.MEMBER, establishment_id=establishment_id)

    result = await creator.create(data, actor)

    assert isinstance(result, UserRead)


async def test_establishment_admin_cannot_create_establishment_admin(
    creator, establishment_id
):
    actor = make_actor(
        establishment_id=establishment_id, role=UserRole.ESTABLISHMENT_ADMIN
    )
    data = make_user_create(
        role=UserRole.ESTABLISHMENT_ADMIN, establishment_id=establishment_id
    )

    with pytest.raises(
        ForbiddenError, match="establishment_admin só pode criar members"
    ):
        await creator.create(data, actor)


async def test_establishment_admin_creates_user_in_provided_establishment(
    creator, mock_membership_repo, establishment_id
):
    actor = make_actor(
        establishment_id=establishment_id, role=UserRole.ESTABLISHMENT_ADMIN
    )
    data = make_user_create(role=UserRole.MEMBER, establishment_id=establishment_id)

    await creator.create(data, actor)

    membership_arg = mock_membership_repo.add.call_args.kwargs["membership"]
    assert membership_arg.establishment_id == establishment_id


async def test_member_cannot_create_any_user(creator, establishment_id):
    actor = make_actor(establishment_id=establishment_id, role=UserRole.MEMBER)
    data = make_user_create(role=UserRole.MEMBER, establishment_id=establishment_id)

    with pytest.raises(
        ForbiddenError, match="Usuário não pode criar usuários nesse estabelecimento"
    ):
        await creator.create(data, actor)


async def test_create_raises_conflict_on_duplicate_email(
    creator, mock_repo, establishment_id
):
    actor = make_actor(
        establishment_id=establishment_id, role=UserRole.ESTABLISHMENT_ADMIN
    )
    data = make_user_create(role=UserRole.MEMBER, establishment_id=establishment_id)
    mock_repo.create.side_effect = IntegrityError(None, None, Exception())

    with pytest.raises(ConflictError, match="E-mail já está em uso."):
        await creator.create(data, actor)


async def test_create_hashes_password(creator, mock_repo, establishment_id):
    actor = make_actor(is_global_admin=True)
    data = make_user_create(role=UserRole.MEMBER, establishment_id=establishment_id)

    await creator.create(data, actor)

    created_arg = mock_repo.create.call_args[0][0]
    assert created_arg.password_hash != data.password
    assert len(created_arg.password_hash) > 0
