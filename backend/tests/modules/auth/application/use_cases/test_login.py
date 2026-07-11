import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import UnauthorizedError
from app.modules.auth.application.dtos.commands import LoginCommand
from app.modules.auth.application.use_cases.login import AuthLogin
from app.modules.auth.domain.entities import TokenPair
from app.modules.users.domain.entities import User
from tests.modules.auth.application.use_cases.conftest import FakeAuthUnitOfWork


@pytest.fixture
def mock_user() -> User:
    user = MagicMock(spec=User)
    user.id = uuid.uuid7()
    user.password_hash = "hashed_password_mock"
    user.is_active = True
    return user


@pytest.fixture
def login_command() -> LoginCommand:
    return LoginCommand(username="teste@email.com", password="senha_super_secreta")


@pytest.fixture
def auth_login(uow: FakeAuthUnitOfWork) -> AuthLogin:
    return AuthLogin(uow=uow)


@patch("app.modules.auth.application.use_cases.login.create_refresh_token")
@patch("app.modules.auth.application.use_cases.login.create_access_token")
@patch("app.modules.auth.application.use_cases.login.verify_password")
async def test_login_success(
    mock_verify_password,
    mock_create_access,
    mock_create_refresh,
    auth_login,
    login_command,
    mock_users_repo: AsyncMock,
    mock_user,
):
    """Testa o cenário ideal onde as credenciais estão corretas e o usuário está ativo."""

    mock_users_repo.get_by_email_or_none.return_value = mock_user
    mock_verify_password.return_value = True
    mock_create_access.return_value = "fake_access_token"
    mock_create_refresh.return_value = "fake_refresh_token"

    result = await auth_login.login(login_command)

    mock_users_repo.get_by_email_or_none.assert_called_once_with(
        login_command.username
    )
    mock_verify_password.assert_called_once_with(
        login_command.password, mock_user.password_hash
    )

    assert isinstance(result, TokenPair)
    assert result.access_token == "fake_access_token"
    assert result.refresh_token == "fake_refresh_token"


async def test_login_raises_error_when_user_not_found(
    auth_login, login_command, mock_users_repo
):
    """Testa falha de login quando o e-mail não existe no banco."""

    mock_users_repo.get_by_email_or_none.return_value = None

    with pytest.raises(UnauthorizedError, match=r"Credenciais inválidas\."):
        await auth_login.login(login_command)

    mock_users_repo.get_by_email_or_none.assert_called_once_with(
        login_command.username
    )


@patch("app.modules.auth.application.use_cases.login.verify_password")
async def test_login_raises_error_on_invalid_password(
    mock_verify_password, auth_login, login_command, mock_users_repo, mock_user
):
    """Testa falha de login quando a senha enviada está errada."""

    mock_users_repo.get_by_email_or_none.return_value = mock_user
    mock_verify_password.return_value = False

    with pytest.raises(UnauthorizedError, match=r"Credenciais inválidas\."):
        await auth_login.login(login_command)


@patch("app.modules.auth.application.use_cases.login.verify_password")
async def test_login_raises_error_when_user_is_inactive(
    mock_verify_password, auth_login, login_command, mock_users_repo, mock_user
):
    """Testa falha de login quando as credenciais batem, mas o usuário está inativo."""

    mock_verify_password.return_value = True
    mock_user.is_active = False
    mock_users_repo.get_by_email_or_none.return_value = mock_user

    with pytest.raises(UnauthorizedError, match=r"Usuário inativo\."):
        await auth_login.login(login_command)
