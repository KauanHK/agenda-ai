import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.roles import UserRole
from app.modules.users.adapters.db.models import User as UserModel
from app.modules.users.adapters.db.repository import UsersRepository
from app.modules.users.application.dtos.filters import UserFilters
from app.modules.users.domain.entities import User, UserExpanded


def make_user_model(**overrides) -> UserModel:
    defaults = {
        "id": uuid.uuid7(),
        "name": "Usuario Teste",
        "email": "usuario@email.com",
        "phone": None,
        "password_hash": "hashed",
        "is_global_admin": False,
        "is_active": True,
    }
    defaults.update(overrides)
    return UserModel(**defaults)


@pytest.fixture
def session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repo(session: AsyncMock) -> UsersRepository:
    return UsersRepository(session)


async def test_get_by_email_or_none_returns_user(repo, session):
    row = make_user_model()
    mock_result = MagicMock()
    mock_result.scalars.return_value.one_or_none.return_value = row
    session.execute.return_value = mock_result

    result = await repo.get_by_email_or_none(row.email)

    assert isinstance(result, User)
    assert result.email == row.email


async def test_get_by_email_or_none_returns_none_when_not_found(repo, session):
    mock_result = MagicMock()
    mock_result.scalars.return_value.one_or_none.return_value = None
    session.execute.return_value = mock_result

    result = await repo.get_by_email_or_none("missing@email.com")

    assert result is None


async def test_get_by_email_returns_user(repo, session):
    row = make_user_model()
    mock_result = MagicMock()
    mock_result.scalars.return_value.one_or_none.return_value = row
    session.execute.return_value = mock_result

    result = await repo.get_by_email(row.email)

    assert isinstance(result, User)


async def test_get_by_email_raises_not_found(repo, session):
    mock_result = MagicMock()
    mock_result.scalars.return_value.one_or_none.return_value = None
    session.execute.return_value = mock_result

    with pytest.raises(NotFoundError):
        await repo.get_by_email("missing@email.com")


async def test_get_by_id_expanded_returns_user_expanded(repo, session):
    row = make_user_model()
    row.memberships = []
    mock_result = MagicMock()
    mock_result.scalars.return_value.one_or_none.return_value = row
    session.execute.return_value = mock_result

    result = await repo.get_by_id_expanded(row.id)

    assert isinstance(result, UserExpanded)
    assert result.memberships == []


async def test_get_by_id_expanded_raises_not_found(repo, session):
    mock_result = MagicMock()
    mock_result.scalars.return_value.one_or_none.return_value = None
    session.execute.return_value = mock_result

    with pytest.raises(NotFoundError):
        await repo.get_by_id_expanded(uuid.uuid7())


def test_apply_filters_with_q(repo):
    stmt = repo._apply_filters(select(UserModel), UserFilters(q="usuario"))

    assert "like" in str(stmt).lower()


def test_apply_filters_with_role_joins_memberships(repo):
    stmt = repo._apply_filters(
        select(UserModel), UserFilters(role=UserRole.MEMBER, is_active=None)
    )

    assert "JOIN" in str(stmt)
