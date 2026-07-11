import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import UnauthorizedError
from app.modules.auth.application.dtos.commands import RefreshCommand
from app.modules.auth.application.use_cases.refresh import AuthRefresh
from app.modules.auth.domain.entities import TokenPair
from app.modules.users.domain.entities import User
from tests.modules.auth.application.use_cases.conftest import FakeAuthUnitOfWork


@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.uuid7()


@pytest.fixture
def mock_user(user_id) -> User:
    user = MagicMock(spec=User)
    user.id = user_id
    user.is_active = True
    return user


@pytest.fixture
def refresh_command() -> RefreshCommand:
    return RefreshCommand(refresh_token="valid.refresh.token")


@pytest.fixture
def valid_claims(user_id) -> dict:
    return {
        "sub": str(user_id),
        "type": "refresh",
    }


@pytest.fixture
def auth_refresh(uow: FakeAuthUnitOfWork) -> AuthRefresh:
    return AuthRefresh(uow=uow)


@patch("app.modules.auth.application.use_cases.refresh.create_refresh_token")
@patch("app.modules.auth.application.use_cases.refresh.create_access_token")
@patch("app.modules.auth.application.use_cases.refresh.decode_refresh_token")
async def test_refresh_success(
    mock_decode_token,
    mock_create_access,
    mock_create_refresh,
    auth_refresh,
    refresh_command,
    valid_claims,
    mock_users_repo: AsyncMock,
    mock_user,
    user_id,
):
    """Testa o cenário ideal onde o refresh token é válido e o usuário está ativo."""

    mock_decode_token.return_value = valid_claims
    mock_create_access.return_value = "new_access_token"
    mock_create_refresh.return_value = "new_refresh_token"
    mock_users_repo.get_by_id_or_none.return_value = mock_user

    result = await auth_refresh.refresh(refresh_command)

    mock_decode_token.assert_called_once_with(refresh_command.refresh_token)
    mock_users_repo.get_by_id_or_none.assert_called_once_with(user_id)

    assert isinstance(result, TokenPair)
    assert result.access_token == "new_access_token"
    assert result.refresh_token == "new_refresh_token"


@patch("app.modules.auth.application.use_cases.refresh.decode_refresh_token")
async def test_refresh_raises_error_on_invalid_token_type(
    mock_decode_token, auth_refresh, refresh_command, mock_users_repo
):
    """Testa falha quando um access token é enviado no lugar de um refresh token."""

    mock_decode_token.side_effect = UnauthorizedError("Token inválido.")

    with pytest.raises(UnauthorizedError, match=r"Token inválido\."):
        await auth_refresh.refresh(refresh_command)

    mock_users_repo.get_by_id_or_none.assert_not_called()


@patch("app.modules.auth.application.use_cases.refresh.decode_refresh_token")
async def test_refresh_raises_error_when_user_not_found(
    mock_decode_token, auth_refresh, refresh_command, valid_claims, mock_users_repo, user_id
):
    """Testa falha quando o token é válido, mas o usuário não existe mais no banco."""

    mock_decode_token.return_value = valid_claims
    mock_users_repo.get_by_id_or_none.return_value = None

    with pytest.raises(UnauthorizedError, match=r"Usuário inativo ou não encontrado\."):
        await auth_refresh.refresh(refresh_command)

    mock_users_repo.get_by_id_or_none.assert_called_once_with(user_id)


@patch("app.modules.auth.application.use_cases.refresh.decode_refresh_token")
async def test_refresh_raises_error_when_user_is_inactive(
    mock_decode_token,
    auth_refresh,
    refresh_command,
    valid_claims,
    mock_users_repo,
    mock_user,
    user_id,
):
    """Testa falha quando o token é válido, mas o usuário foi desativado."""

    mock_decode_token.return_value = valid_claims
    mock_user.is_active = False
    mock_users_repo.get_by_id_or_none.return_value = mock_user

    with pytest.raises(UnauthorizedError, match=r"Usuário inativo ou não encontrado\."):
        await auth_refresh.refresh(refresh_command)

    mock_users_repo.get_by_id_or_none.assert_called_once_with(user_id)
