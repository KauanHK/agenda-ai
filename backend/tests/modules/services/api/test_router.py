from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.core.pagination import PaginatedResponse


def test_list_services_route_success(client, mock_services_reader, service_read, establishment_id):
    mock_services_reader.paginate.return_value = PaginatedResponse(
        data=[service_read],
        total=1,
        page=1,
        size=10,
    )

    response = client.get(
        f"/establishments/{establishment_id}/services/",
        params={"page": 1, "size": 10, "q": "corte", "is_active": "true"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] == 1
    assert len(body["data"]) == 1
    assert body["data"][0]["name"] == service_read.name
    mock_services_reader.paginate.assert_awaited_once()


def test_list_services_route_missing_establishment_id(client):
    response = client.get("/establishments/not-a-valid-uuid/services/", params={"page": 1, "size": 10})

    assert response.status_code == 422


def test_get_service_route_success(client, mock_services_reader, service_read, establishment_id):
    mock_services_reader.get_by_id.return_value = service_read

    response = client.get(f"/establishments/{establishment_id}/services/{service_read.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(service_read.id)
    mock_services_reader.get_by_id.assert_awaited_once()


def test_get_service_route_not_found(client, mock_services_reader, service_read, establishment_id):
    mock_services_reader.get_by_id.side_effect = NotFoundError("Acesso negado.")

    response = client.get(f"/establishments/{establishment_id}/services/{service_read.id}")

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_get_service_route_invalid_uuid(client, establishment_id):
    response = client.get(f"/establishments/{establishment_id}/services/invalid-uuid")

    assert response.status_code == 422


def test_create_service_route_success(client, mock_services_creator, service_read, establishment_id):
    mock_services_creator.create.return_value = service_read

    payload = {
        "name": service_read.name,
        "description": service_read.description,
        "duration_minutes": service_read.duration_minutes,
        "price": str(service_read.price),
    }

    response = client.post(f"/establishments/{establishment_id}/services/", json=payload)

    assert response.status_code == 201, response.text
    assert response.json()["name"] == service_read.name
    mock_services_creator.create.assert_awaited_once()


def test_create_service_route_without_description(
    client, mock_services_creator, service_read, establishment_id
):
    service_read_no_desc = service_read.model_copy(update={"description": None})
    mock_services_creator.create.return_value = service_read_no_desc

    payload = {
        "name": "Sem Descrição",
        "duration_minutes": 45,
        "price": "75.00",
    }

    response = client.post(f"/establishments/{establishment_id}/services/", json=payload)

    assert response.status_code == 201
    assert response.json()["description"] is None


def test_create_service_route_validation_error_missing_name(client, establishment_id):
    response = client.post(
        f"/establishments/{establishment_id}/services/",
        json={"duration_minutes": 30, "price": "10.00"},
    )
    assert response.status_code == 422


def test_create_service_route_validation_error_missing_duration(client, establishment_id):
    response = client.post(
        f"/establishments/{establishment_id}/services/",
        json={"name": "X", "price": "10.00"},
    )
    assert response.status_code == 422


def test_create_service_route_validation_error_missing_price(client, establishment_id):
    response = client.post(
        f"/establishments/{establishment_id}/services/",
        json={"name": "X", "duration_minutes": 30},
    )
    assert response.status_code == 422


def test_create_service_route_validation_error_zero_duration(client, establishment_id):
    response = client.post(
        f"/establishments/{establishment_id}/services/",
        json={"name": "X", "duration_minutes": 0, "price": "10.00"},
    )
    assert response.status_code == 422


def test_create_service_route_validation_error_negative_duration(client, establishment_id):
    response = client.post(
        f"/establishments/{establishment_id}/services/",
        json={"name": "X", "duration_minutes": -5, "price": "10.00"},
    )
    assert response.status_code == 422


def test_create_service_route_validation_error_negative_price(client, establishment_id):
    response = client.post(
        f"/establishments/{establishment_id}/services/",
        json={"name": "X", "duration_minutes": 30, "price": "-1.00"},
    )
    assert response.status_code == 422


def test_create_service_route_validation_error_empty_name(client, establishment_id):
    response = client.post(
        f"/establishments/{establishment_id}/services/",
        json={"name": "", "duration_minutes": 30, "price": "10.00"},
    )
    assert response.status_code == 422


def test_create_service_route_conflict(client, mock_services_creator, establishment_id):
    mock_services_creator.create.side_effect = ConflictError(
        "Já existe um serviço com este nome neste estabelecimento."
    )

    response = client.post(
        f"/establishments/{establishment_id}/services/",
        json={"name": "Corte", "duration_minutes": 30, "price": "10.00"},
    )

    assert response.status_code == 409
    assert response.json()["code"] == "conflict"


def test_create_service_route_forbidden_for_member(client, mock_services_creator, establishment_id):
    mock_services_creator.create.side_effect = ForbiddenError(
        "Apenas establishment_admin pode escrever serviços."
    )

    response = client.post(
        f"/establishments/{establishment_id}/services/",
        json={"name": "Corte", "duration_minutes": 30, "price": "10.00"},
    )

    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"


def test_create_service_route_forbidden_for_global_admin(client, mock_services_creator, establishment_id):
    mock_services_creator.create.side_effect = ForbiddenError(
        "global_admin não opera sobre serviços."
    )

    response = client.post(
        f"/establishments/{establishment_id}/services/",
        json={"name": "Corte", "duration_minutes": 30, "price": "10.00"},
    )

    assert response.status_code == 403


def test_update_service_route_success(client, mock_services_updater, service_read, establishment_id):
    mock_services_updater.update.return_value = service_read

    response = client.patch(
        f"/establishments/{establishment_id}/services/{service_read.id}",
        json={"name": "Novo Nome"},
    )

    assert response.status_code == 200
    mock_services_updater.update.assert_awaited_once()


def test_update_service_route_not_found(client, mock_services_updater, service_read, establishment_id):
    mock_services_updater.update.side_effect = NotFoundError("Acesso negado.")

    response = client.patch(
        f"/establishments/{establishment_id}/services/{service_read.id}",
        json={"name": "Novo Nome"},
    )

    assert response.status_code == 404


def test_update_service_route_conflict(client, mock_services_updater, service_read, establishment_id):
    mock_services_updater.update.side_effect = ConflictError(
        "Já existe um serviço com este nome neste estabelecimento."
    )

    response = client.patch(
        f"/establishments/{establishment_id}/services/{service_read.id}",
        json={"name": "Existente"},
    )

    assert response.status_code == 409


def test_update_service_route_forbidden_for_member(
    client, mock_services_updater, service_read, establishment_id
):
    mock_services_updater.update.side_effect = ForbiddenError(
        "Apenas establishment_admin pode escrever serviços."
    )

    response = client.patch(
        f"/establishments/{establishment_id}/services/{service_read.id}",
        json={"name": "Novo Nome"},
    )

    assert response.status_code == 403


def test_update_service_route_validation_error_negative_price(client, service_read, establishment_id):
    response = client.patch(
        f"/establishments/{establishment_id}/services/{service_read.id}",
        json={"price": "-1.00"},
    )

    assert response.status_code == 422


def test_update_service_route_validation_error_zero_duration(client, service_read, establishment_id):
    response = client.patch(
        f"/establishments/{establishment_id}/services/{service_read.id}",
        json={"duration_minutes": 0},
    )

    assert response.status_code == 422


def test_activate_service_route_success(client, mock_services_activator, service_read, establishment_id):
    mock_services_activator.activate.return_value = service_read

    response = client.post(f"/establishments/{establishment_id}/services/{service_read.id}/activate")

    assert response.status_code == 200
    assert response.json()["id"] == str(service_read.id)
    mock_services_activator.activate.assert_awaited_once()


def test_activate_service_route_not_found(
    client, mock_services_activator, service_read, establishment_id
):
    mock_services_activator.activate.side_effect = NotFoundError("Service not found.")

    response = client.post(f"/establishments/{establishment_id}/services/{service_read.id}/activate")

    assert response.status_code == 404


def test_activate_service_route_forbidden_for_member(
    client, mock_services_activator, service_read, establishment_id
):
    mock_services_activator.activate.side_effect = ForbiddenError(
        "Apenas establishment_admin pode escrever serviços."
    )

    response = client.post(f"/establishments/{establishment_id}/services/{service_read.id}/activate")

    assert response.status_code == 403


def test_deactivate_service_route_success(
    client, mock_services_activator, service_read, establishment_id
):
    mock_services_activator.deactivate.return_value = service_read

    response = client.post(f"/establishments/{establishment_id}/services/{service_read.id}/deactivate")

    assert response.status_code == 200
    mock_services_activator.deactivate.assert_awaited_once()


def test_deactivate_service_route_forbidden_for_global_admin(
    client, mock_services_activator, service_read, establishment_id
):
    mock_services_activator.deactivate.side_effect = ForbiddenError(
        "global_admin não opera sobre serviços."
    )

    response = client.post(f"/establishments/{establishment_id}/services/{service_read.id}/deactivate")

    assert response.status_code == 403
