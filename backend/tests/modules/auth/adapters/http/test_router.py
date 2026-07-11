import uuid
from datetime import UTC, datetime

from app.core.roles import UserRole
from app.modules.auth.domain.entities import TokenPair
from app.modules.users.domain.entities import User


def make_token_pair() -> TokenPair:
    return TokenPair(
        access_token="mocked_access_token_123",
        refresh_token="mocked_refresh_token_456",
    )


def make_user() -> User:
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


def test_login_route_success(client, mock_auth_login):
    mock_auth_login.login.return_value = make_token_pair()

    payload = {"username": "teste@email.com", "password": "senha_segura"}

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 200

    data = response.json()
    assert data["access_token"] == "mocked_access_token_123"
    assert data["refresh_token"] == "mocked_refresh_token_456"

    mock_auth_login.login.assert_awaited_once()


def test_login_route_validation_error(client):
    payload = {"username": "teste@email.com"}

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "password"]


def test_refresh_route_success(client, mock_auth_refresh):
    mock_auth_refresh.refresh.return_value = make_token_pair()

    payload = {"refresh_token": "token_valido_aqui"}

    response = client.post("/auth/refresh", json=payload)

    assert response.status_code == 200
    assert response.json()["access_token"] == "mocked_access_token_123"
    mock_auth_refresh.refresh.assert_awaited_once()


def test_create_user_route_success(client, mock_auth_creator):
    mock_auth_creator.create.return_value = make_user()

    payload = {
        "name": "Novo Usuário",
        "email": "novo@email.com",
        "password": "senha1234",
        "role": UserRole.MEMBER.value,
        "establishment_id": str(uuid.uuid7()),
    }

    response = client.post("/auth", json=payload)

    assert response.status_code == 201

    data = response.json()
    assert data["email"] == payload["email"]
    mock_auth_creator.create.assert_awaited_once()
