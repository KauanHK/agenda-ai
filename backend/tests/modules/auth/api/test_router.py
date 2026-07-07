import uuid

import pytest

from app.modules.auth.domain.schemas import TokenResponse
from app.modules.users.domain.enums import UserRole
from app.modules.users.domain.schemas import UserRead


@pytest.fixture
def mock_token_response() -> dict:
    return {
        "access_token": "mocked_access_token_123",
        "refresh_token": "mocked_refresh_token_456",
        "token_type": "bearer",
    }


@pytest.fixture
def mock_user_read() -> UserRead:
    return UserRead(
        id=uuid.uuid7(),
        name="Novo Usuário",
        email="novo@email.com",
        phone=None,
        is_active=True,
    )


def test_login_route_success(client, mock_auth_login, mock_token_response):
    mock_auth_login.login.return_value = TokenResponse(**mock_token_response)

    payload = {"username": "teste@email.com", "password": "senha_segura"}

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 200

    data = response.json()
    assert data["access_token"] == mock_token_response["access_token"]
    assert data["refresh_token"] == mock_token_response["refresh_token"]

    mock_auth_login.login.assert_awaited_once()


def test_login_route_validation_error(client):
    payload = {"username": "teste@email.com"}

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "password"]


def test_refresh_route_success(client, mock_auth_refresh, mock_token_response):
    mock_auth_refresh.refresh.return_value = TokenResponse(**mock_token_response)

    payload = {"refresh_token": "token_valido_aqui"}

    response = client.post("/auth/refresh", json=payload)

    assert response.status_code == 200
    assert response.json()["access_token"] == mock_token_response["access_token"]
    mock_auth_refresh.refresh.assert_awaited_once()


def test_create_user_route_success(client, mock_auth_creator, mock_user_read):
    mock_auth_creator.create.return_value = mock_user_read

    payload = {
        "name": "Novo Usuário",
        "email": "novo@email.com",
        "password": "senha1234",
        "role": UserRole.MEMBER.value,
        "establishment_id": str(uuid.uuid7()),
    }

    response = client.post("/auth/", json=payload)

    assert response.status_code == 201

    data = response.json()
    assert data["email"] == payload["email"]
    mock_auth_creator.create.assert_awaited_once()
