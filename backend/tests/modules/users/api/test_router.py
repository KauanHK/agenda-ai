import uuid
from datetime import UTC, datetime

from app.core.pagination import PaginatedResponse
from app.modules.users.domain.expanded import UserReadExpanded
from app.modules.users.domain.schemas import UserRead


def make_user_read() -> UserRead:
    return UserRead(
        id=uuid.uuid7(),
        name="Usuario Teste",
        email="usuario@email.com",
        phone=None,
        is_active=True,
    )


def make_user_read_expanded() -> UserReadExpanded:
    return UserReadExpanded(
        id=uuid.uuid7(),
        name="Usuario Teste",
        email="usuario@email.com",
        phone=None,
        is_active=True,
        is_global_admin=False,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        memberships=[],
    )


def test_get_me_route_success(client, mock_users_reader):
    user = make_user_read()
    mock_users_reader.get_by_id.return_value = user

    response = client.get("/users/me")

    assert response.status_code == 200
    assert response.json()["email"] == user.email
    mock_users_reader.get_by_id.assert_awaited_once()


def test_update_me_route_success(client, mock_users_updater):
    updated = make_user_read()
    mock_users_updater.update_me.return_value = updated

    payload = {
        "name": updated.name,
        "email": updated.email,
    }

    response = client.patch("/users/me", json=payload)

    assert response.status_code == 200
    assert response.json()["name"] == updated.name
    mock_users_updater.update_me.assert_awaited_once()


def test_update_me_route_validation_error_name_too_long(client):
    response = client.patch("/users/me", json={"name": "x" * 256})

    assert response.status_code == 422


def test_list_users_route_success(client, mock_users_reader):
    user = make_user_read()
    mock_users_reader.paginate.return_value = PaginatedResponse(
        data=[user],
        total=1,
        page=1,
        size=10,
    )

    response = client.get(
        "/users/",
        params={
            "page": 1,
            "size": 10,
            "q": "joao",
            "role": "member",
            "is_active": "true",
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["total"] == 1
    assert len(data["data"]) == 1
    mock_users_reader.paginate.assert_awaited_once()


def test_get_user_route_success(client, mock_users_reader):
    user = make_user_read_expanded()
    mock_users_reader.get_by_id.return_value = user

    response = client.get(f"/users/{user.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(user.id)
    mock_users_reader.get_by_id.assert_awaited_once()


def test_get_user_route_invalid_uuid(client):
    response = client.get("/users/invalid-uuid")

    assert response.status_code == 422


def test_update_user_route_success(client, mock_users_updater):
    user = make_user_read()
    mock_users_updater.update.return_value = user

    response = client.patch(f"/users/{user.id}", json={"name": user.name})

    assert response.status_code == 200
    assert response.json()["name"] == user.name
    mock_users_updater.update.assert_awaited_once()


def test_activate_user_route_success(client, mock_users_activator):
    user = make_user_read()
    mock_users_activator.activate.return_value = user

    response = client.post(f"/users/{user.id}/activate")

    assert response.status_code == 200
    assert response.json()["id"] == str(user.id)
    mock_users_activator.activate.assert_awaited_once()


def test_deactivate_user_route_success(client, mock_users_activator):
    user = make_user_read()
    mock_users_activator.deactivate.return_value = user

    response = client.post(f"/users/{user.id}/deactivate")

    assert response.status_code == 200
    assert response.json()["id"] == str(user.id)
    mock_users_activator.deactivate.assert_awaited_once()
