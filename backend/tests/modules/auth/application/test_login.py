import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import UnauthorizedError
from app.db.unit_of_work import UnitOfWork
from app.modules.auth.application.login import AuthLogin
from app.modules.auth.domain.schemas import LoginRequest, TokenResponse
from app.modules.users.domain.enums import UserRole
from app.modules.users.domain.model import User
from app.modules.users.infra.repository import UsersRepository


@pytest.fixture
def establishment_id() -> uuid.UUID:
    return uuid.uuid7()


@pytest.fixture
def mock_user(establishment_id) -> User:
    user = MagicMock(spec=User)
    user.id = uuid.uuid7()
    user.password_hash = "hashed_password_mock"
    user.is_active = True
    return user


@pytest.fixture
def login_request() -> LoginRequest:
    return LoginRequest(username="teste@email.com", password="senha_super_secreta")


@pytest.fixture
def mock_repo(mock_user) -> AsyncMock:
    repo = AsyncMock(spec=UsersRepository)
    repo.get_by_email_or_none.return_value = mock_user
    return repo


@pytest.fixture
def mock_uow(mock_repo) -> AsyncMock:
    uow = AsyncMock(spec=UnitOfWork)

    uow.__aenter__.return_value = uow
    uow.__aexit__.return_value = None
    uow.repository.return_value = mock_repo
    return uow


@pytest.fixture
def auth_login(mock_uow) -> AuthLogin:
    return AuthLogin(uow=mock_uow)


@patch("app.modules.auth.application.login.create_refresh_token")
@patch("app.modules.auth.application.login.create_access_token")
@patch("app.modules.auth.application.login.verify_password")
async def test_login_success(
    mock_verify_password,
    mock_create_access,
    mock_create_refresh,
    auth_login,
    login_request,
    mock_repo,
    mock_user,
):
    """Testa o cenário ideal onde as credenciais estão corretas e o usuário está ativo."""

    # Arrange
    mock_verify_password.return_value = True
    mock_create_access.return_value = "fake_access_token"
    mock_create_refresh.return_value = "fake_refresh_token"

    # Act
    result = await auth_login.login(login_request)

    # Assert
    mock_repo.get_by_email_or_none.assert_called_once_with(login_request.username)
    mock_verify_password.assert_called_once_with(
        login_request.password, mock_user.password_hash
    )

    assert isinstance(result, TokenResponse)
    assert result.access_token == "fake_access_token"
    assert result.refresh_token == "fake_refresh_token"


async def test_login_raises_error_when_user_not_found(
    auth_login, login_request, mock_repo
):
    """Testa falha de login quando o e-mail não existe no banco."""

    # Arrange
    mock_repo.get_by_email_or_none.return_value = None

    # Act & Assert
    with pytest.raises(UnauthorizedError, match="Credenciais inválidas."):
        await auth_login.login(login_request)

    mock_repo.get_by_email_or_none.assert_called_once_with(login_request.username)


@patch("app.modules.auth.application.login.verify_password")
async def test_login_raises_error_on_invalid_password(
    mock_verify_password, auth_login, login_request, mock_repo
):
    """Testa falha de login quando a senha enviada está errada."""

    # Arrange
    mock_verify_password.return_value = False

    # Act & Assert
    with pytest.raises(UnauthorizedError, match="Credenciais inválidas."):
        await auth_login.login(login_request)

    mock_repo.get_by_email_or_none.assert_called_once_with(login_request.username)


@patch("app.modules.auth.application.login.verify_password")
async def test_login_raises_error_when_user_is_inactive(
    mock_verify_password, auth_login, login_request, mock_user
):
    """Testa falha de login quando as credenciais batem, mas o usuário está inativo."""

    # Arrange
    mock_verify_password.return_value = True
    mock_user.is_active = False  # Força o usuário a estar inativo

    # Act & Assert
    with pytest.raises(UnauthorizedError, match="Usuário inativo."):
        await auth_login.login(login_request)
