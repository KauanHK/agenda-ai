import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import UnauthorizedError
from app.db.unit_of_work import UnitOfWork
from app.modules.auth.application.refresh import AuthRefresh
from app.modules.auth.domain.schemas import RefreshRequest, TokenResponse
from app.modules.users.domain.model import User
from app.modules.users.infra.repository import UsersRepository


@pytest.fixture
def establishment_id() -> uuid.UUID:
    return uuid.uuid7()


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
def refresh_request() -> RefreshRequest:
    return RefreshRequest(refresh_token="valid.refresh.token")


@pytest.fixture
def valid_claims(user_id) -> dict:
    return {
        "sub": str(user_id),
        "type": "refresh",
        "establishment_id": "algum-id",
        "role": "member",
    }


@pytest.fixture
def mock_repo(mock_user) -> AsyncMock:
    repo = AsyncMock(spec=UsersRepository)
    repo.get_by_id_or_none.return_value = mock_user
    return repo


@pytest.fixture
def mock_uow(mock_repo) -> AsyncMock:
    uow = AsyncMock(spec=UnitOfWork)
    uow.__aenter__.return_value = uow
    uow.__aexit__.return_value = None
    uow.repository.return_value = mock_repo
    return uow


@pytest.fixture
def auth_refresh(mock_uow) -> AuthRefresh:
    return AuthRefresh(uow=mock_uow)


@patch("app.modules.auth.application.refresh.create_refresh_token")
@patch("app.modules.auth.application.refresh.create_access_token")
@patch("app.modules.auth.application.refresh.decode_refresh_token")
async def test_refresh_success(
    mock_decode_token,
    mock_create_access,
    mock_create_refresh,
    auth_refresh,
    refresh_request,
    valid_claims,
    mock_repo,
    user_id,
):
    """Testa o cenário ideal onde o refresh token é válido e o usuário está ativo."""

    # Arrange
    mock_decode_token.return_value = valid_claims
    mock_create_access.return_value = "new_access_token"
    mock_create_refresh.return_value = "new_refresh_token"

    # Act
    result = await auth_refresh.refresh(refresh_request)

    # Assert
    mock_decode_token.assert_called_once_with(refresh_request.refresh_token)
    mock_repo.get_by_id_or_none.assert_called_once_with(user_id)

    assert isinstance(result, TokenResponse)
    assert result.access_token == "new_access_token"
    assert result.refresh_token == "new_refresh_token"


@patch("app.modules.auth.application.refresh.decode_refresh_token")
async def test_refresh_raises_error_on_invalid_token_type(
    mock_decode_token, auth_refresh, refresh_request, valid_claims, mock_repo
):
    """Testa falha quando um access token é enviado no lugar de um refresh token."""

    # Arrange
    invalid_claims = valid_claims.copy()
    invalid_claims["type"] = "access"  # Simulando um token do tipo errado
    mock_decode_token.side_effect = UnauthorizedError("Token inválido.")

    # Act & Assert
    with pytest.raises(UnauthorizedError, match="Token inválido."):
        await auth_refresh.refresh(refresh_request)

    # Verifica que o repositório nem chegou a ser chamado, pois falhou antes
    mock_repo.get_by_id_or_none.assert_not_called()


@patch("app.modules.auth.application.refresh.decode_refresh_token")
async def test_refresh_raises_error_when_user_not_found(
    mock_decode_token, auth_refresh, refresh_request, valid_claims, mock_repo, user_id
):
    """Testa falha quando o token é válido, mas o usuário não existe mais no banco."""

    # Arrange
    mock_decode_token.return_value = valid_claims
    mock_repo.get_by_id_or_none.return_value = None

    # Act & Assert
    with pytest.raises(UnauthorizedError, match="Usuário inativo ou não encontrado."):
        await auth_refresh.refresh(refresh_request)

    mock_repo.get_by_id_or_none.assert_called_once_with(user_id)


@patch("app.modules.auth.application.refresh.decode_refresh_token")
async def test_refresh_raises_error_when_user_is_inactive(
    mock_decode_token,
    auth_refresh,
    refresh_request,
    valid_claims,
    mock_repo,
    mock_user,
    user_id,
):
    """Testa falha quando o token é válido, mas o usuário foi desativado."""

    # Arrange
    mock_decode_token.return_value = valid_claims
    mock_user.is_active = False  # Força o usuário a estar inativo

    # Act & Assert
    with pytest.raises(UnauthorizedError, match="Usuário inativo ou não encontrado."):
        await auth_refresh.refresh(refresh_request)

    mock_repo.get_by_id_or_none.assert_called_once_with(user_id)
