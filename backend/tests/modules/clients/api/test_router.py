from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.core.pagination import PaginatedResponse


def test_list_clients_route_success(
    client, mock_clients_reader, client_read, establishment_id
):
    mock_clients_reader.paginate.return_value = PaginatedResponse(
        data=[client_read],
        total=1,
        page=1,
        size=10,
    )

    response = client.get(
        f"/establishments/{establishment_id}/clients",
        params={"page": 1, "size": 10, "q": "cli", "is_active": "true"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] == 1
    assert len(body["data"]) == 1
    assert body["data"][0]["name"] == client_read.name
    mock_clients_reader.paginate.assert_awaited_once()


def test_get_client_route_success(
    client, mock_clients_reader, client_read, establishment_id
):
    mock_clients_reader.get_by_id.return_value = client_read

    response = client.get(f"/establishments/{establishment_id}/clients/{client_read.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(client_read.id)
    mock_clients_reader.get_by_id.assert_awaited_once()


def test_get_client_route_not_found(
    client, mock_clients_reader, client_read, establishment_id
):
    mock_clients_reader.get_by_id.side_effect = NotFoundError("Acesso negado.")

    response = client.get(f"/establishments/{establishment_id}/clients/{client_read.id}")

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_get_client_route_invalid_uuid(client, establishment_id):
    response = client.get(f"/establishments/{establishment_id}/clients/invalid-uuid")

    assert response.status_code == 422


def test_create_client_route_success(
    client, mock_clients_creator, client_read, establishment_id
):
    mock_clients_creator.create.return_value = client_read

    payload = {
        "name": client_read.name,
        "phone": client_read.phone,
        "email": client_read.email,
    }

    response = client.post(f"/establishments/{establishment_id}/clients/", json=payload)

    assert response.status_code == 201, response.text
    assert response.json()["name"] == client_read.name
    mock_clients_creator.create.assert_awaited_once()


def test_create_client_route_without_email(
    client, mock_clients_creator, client_read, establishment_id
):
    client_read_no_email = client_read.model_copy(update={"email": None})
    mock_clients_creator.create.return_value = client_read_no_email

    payload = {"name": "Sem Email", "phone": "11999998888"}

    response = client.post(f"/establishments/{establishment_id}/clients/", json=payload)

    assert response.status_code == 201
    assert response.json()["email"] is None


def test_create_client_route_validation_error_missing_name(client, establishment_id):
    response = client.post(
        f"/establishments/{establishment_id}/clients/",
        json={"phone": "11999990000"},
    )
    assert response.status_code == 422


def test_create_client_route_validation_error_missing_phone(client, establishment_id):
    response = client.post(
        f"/establishments/{establishment_id}/clients/",
        json={"name": "Cliente"},
    )
    assert response.status_code == 422


def test_create_client_route_validation_error_empty_phone(client, establishment_id):
    response = client.post(
        f"/establishments/{establishment_id}/clients/",
        json={"name": "Cliente", "phone": ""},
    )
    assert response.status_code == 422


def test_create_client_route_validation_error_invalid_email(client, establishment_id):
    response = client.post(
        f"/establishments/{establishment_id}/clients/",
        json={"name": "Cliente", "phone": "11999990000", "email": "not-an-email"},
    )
    assert response.status_code == 422


def test_create_client_route_conflict(client, mock_clients_creator, establishment_id):
    mock_clients_creator.create.side_effect = ConflictError(
        "Telefone ou e-mail já cadastrado neste estabelecimento."
    )

    response = client.post(
        f"/establishments/{establishment_id}/clients/",
        json={"name": "Cliente", "phone": "11999990000"},
    )

    assert response.status_code == 409
    assert response.json()["code"] == "conflict"


def test_create_client_route_forbidden_for_member(
    client, mock_clients_creator, establishment_id
):
    mock_clients_creator.create.side_effect = ForbiddenError(
        "Apenas establishment_admin pode escrever clientes."
    )

    response = client.post(
        f"/establishments/{establishment_id}/clients/",
        json={"name": "Cliente", "phone": "11999990000"},
    )

    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"


def test_create_client_route_forbidden_for_global_admin(
    client, mock_clients_creator, establishment_id
):
    mock_clients_creator.create.side_effect = ForbiddenError(
        "global_admin não opera sobre clientes."
    )

    response = client.post(
        f"/establishments/{establishment_id}/clients/",
        json={"name": "Cliente", "phone": "11999990000"},
    )

    assert response.status_code == 403


def test_update_client_route_success(
    client, mock_clients_updater, client_read, establishment_id
):
    mock_clients_updater.update.return_value = client_read

    response = client.patch(
        f"/establishments/{establishment_id}/clients/{client_read.id}",
        json={"name": "Novo Nome"},
    )

    assert response.status_code == 200
    mock_clients_updater.update.assert_awaited_once()


def test_update_client_route_not_found(
    client, mock_clients_updater, client_read, establishment_id
):
    mock_clients_updater.update.side_effect = NotFoundError("Acesso negado.")

    response = client.patch(
        f"/establishments/{establishment_id}/clients/{client_read.id}",
        json={"name": "Novo Nome"},
    )

    assert response.status_code == 404


def test_update_client_route_conflict(
    client, mock_clients_updater, client_read, establishment_id
):
    mock_clients_updater.update.side_effect = ConflictError(
        "Telefone ou e-mail já cadastrado neste estabelecimento."
    )

    response = client.patch(
        f"/establishments/{establishment_id}/clients/{client_read.id}",
        json={"phone": "11999991111"},
    )

    assert response.status_code == 409


def test_update_client_route_forbidden_for_member(
    client, mock_clients_updater, client_read, establishment_id
):
    mock_clients_updater.update.side_effect = ForbiddenError(
        "Apenas establishment_admin pode escrever clientes."
    )

    response = client.patch(
        f"/establishments/{establishment_id}/clients/{client_read.id}",
        json={"name": "Novo Nome"},
    )

    assert response.status_code == 403


def test_activate_client_route_success(
    client, mock_clients_activator, client_read, establishment_id
):
    mock_clients_activator.activate.return_value = client_read

    response = client.post(
        f"/establishments/{establishment_id}/clients/{client_read.id}/activate",
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(client_read.id)
    mock_clients_activator.activate.assert_awaited_once()


def test_activate_client_route_not_found(
    client, mock_clients_activator, client_read, establishment_id
):
    mock_clients_activator.activate.side_effect = NotFoundError("Client not found.")

    response = client.post(
        f"/establishments/{establishment_id}/clients/{client_read.id}/activate",
    )

    assert response.status_code == 404


def test_activate_client_route_forbidden_for_member(
    client, mock_clients_activator, client_read, establishment_id
):
    mock_clients_activator.activate.side_effect = ForbiddenError(
        "Apenas establishment_admin pode escrever clientes."
    )

    response = client.post(
        f"/establishments/{establishment_id}/clients/{client_read.id}/activate",
    )

    assert response.status_code == 403


def test_deactivate_client_route_success(
    client, mock_clients_activator, client_read, establishment_id
):
    mock_clients_activator.deactivate.return_value = client_read

    response = client.post(
        f"/establishments/{establishment_id}/clients/{client_read.id}/deactivate",
    )

    assert response.status_code == 200
    mock_clients_activator.deactivate.assert_awaited_once()


def test_deactivate_client_route_forbidden_for_global_admin(
    client, mock_clients_activator, client_read, establishment_id
):
    mock_clients_activator.deactivate.side_effect = ForbiddenError(
        "global_admin não opera sobre clientes."
    )

    response = client.post(
        f"/establishments/{establishment_id}/clients/{client_read.id}/deactivate",
    )

    assert response.status_code == 403
