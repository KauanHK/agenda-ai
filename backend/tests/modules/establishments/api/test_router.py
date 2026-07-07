from unittest.mock import ANY

from app.core.pagination import PaginatedResponse


def test_create_establishment_route_success(client, mock_creator, establishment_read):
    mock_creator.create.return_value = establishment_read

    payload = {
        "name": "Clínica Nova",
        "document": "11222333000181",
        "document_type": "cnpj",
        "is_active": True,
        "timezone": "America/Sao_Paulo",
        "street": "Rua das Flores",
        "number": "123",
        "complement": "",
        "neighborhood": "Centro",
        "city": "São Paulo",
        "state": "SP",
        "zip_code": "01310100",
    }

    response = client.post("/establishments/", json=payload)

    assert response.status_code == 201
    assert response.json()["name"] == establishment_read.name
    assert response.json()["document"] == establishment_read.document
    mock_creator.create.assert_awaited_once()


def test_create_establishment_route_validation_error(client):
    payload = {
        "name": "Clínica Nova",
        "document": "123",
        "timezone": "America/Sao_Paulo",
    }

    response = client.post("/establishments/", json=payload)

    assert response.status_code == 422


def test_list_establishments_route_success(client, mock_reader, establishment_read):
    mock_reader.paginate.return_value = PaginatedResponse(
        data=[establishment_read],
        total=1,
        page=1,
        size=10,
    )

    response = client.get(
        "/establishments/",
        params={
            "page": 1,
            "size": 10,
            "name": "Clínica",
            "cnpj": "11222333000181",
            "timezone": "America/Sao_Paulo",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["data"]) == 1
    mock_reader.paginate.assert_awaited_once()


def test_get_establishment_route_success(client, mock_reader, establishment_read):
    mock_reader.get_by_id.return_value = establishment_read

    response = client.get(f"/establishments/{establishment_read.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(establishment_read.id)
    mock_reader.get_by_id.assert_awaited_once_with(
        establishment_id=establishment_read.id, actor=ANY
    )


def test_get_establishment_route_invalid_uuid(client):
    response = client.get("/establishments/invalid-uuid")

    assert response.status_code == 422


def test_update_establishment_route_success(client, mock_updater, establishment_read):
    mock_updater.update.return_value = establishment_read

    payload = {
        "name": "Clínica Atualizada",
        "document": "11222333000181",
        "timezone": "America/Rio_Branco",
    }

    response = client.patch(f"/establishments/{establishment_read.id}", json=payload)

    assert response.status_code == 200
    assert response.json()["name"] == establishment_read.name
    mock_updater.update.assert_awaited_once()


def test_update_establishment_route_validation_error(client, establishment_read):
    payload = {
        "name": "Clínica Atualizada",
        "document": "123",
        "timezone": "America/Rio_Branco",
    }

    response = client.patch(f"/establishments/{establishment_read.id}", json=payload)

    assert response.status_code == 422


def test_delete_establishment_route_success(client, mock_deleter, establishment_read):
    response = client.delete(f"/establishments/{establishment_read.id}")

    assert response.status_code == 204
    assert response.content == b""
    mock_deleter.delete.assert_awaited_once_with(establishment_read.id)


def test_activate_establishment_route_success(
    client, mock_activator, establishment_read
):
    mock_activator.activate.return_value = establishment_read

    response = client.post(f"/establishments/{establishment_read.id}/activate")

    assert response.status_code == 200
    assert response.json()["id"] == str(establishment_read.id)
    mock_activator.activate.assert_awaited_once_with(establishment_read.id)


def test_deactivate_establishment_route_success(
    client, mock_activator, establishment_read
):
    mock_activator.deactivate.return_value = establishment_read

    response = client.post(f"/establishments/{establishment_read.id}/deactivate")

    assert response.status_code == 200
    assert response.json()["id"] == str(establishment_read.id)
    mock_activator.deactivate.assert_awaited_once_with(establishment_read.id)
