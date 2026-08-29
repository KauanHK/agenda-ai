import uuid

from app.core.exceptions import ConflictError, NotFoundError
from app.core.pagination.params import Page


def make_create_payload() -> dict:
    return {
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


def test_create_establishment_route_success(client, mock_creator, establishment):
    mock_creator.create.return_value = establishment

    response = client.post("/establishments", json=make_create_payload())

    assert response.status_code == 201, response.text
    assert response.json()["name"] == establishment.name
    assert response.json()["document"] == establishment.document
    mock_creator.create.assert_awaited_once()


def test_create_establishment_route_validation_error(client):
    payload = {
        "name": "Clínica Nova",
        "document": "123",
        "timezone": "America/Sao_Paulo",
    }

    response = client.post("/establishments", json=payload)

    assert response.status_code == 422


def test_create_establishment_route_conflict(client, mock_creator):
    mock_creator.create.side_effect = ConflictError(
        "Já existe um estabelecimento com este cpf/cnpj."
    )

    response = client.post("/establishments", json=make_create_payload())

    assert response.status_code == 409


def test_list_establishments_route_success(client, mock_paginator, establishment):
    mock_paginator.paginate.return_value = Page(
        items=[establishment], total=1, page=1, page_size=10
    )

    response = client.get(
        "/establishments",
        params={"page": 1, "size": 10, "name": "Clínica"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] == 1
    assert len(body["data"]) == 1
    assert body["data"][0]["id"] == str(establishment.id)


def test_get_establishment_route_success(client, mock_reader, establishment):
    mock_reader.get_by_id.return_value = establishment

    response = client.get(f"/establishments/{establishment.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(establishment.id)


def test_get_establishment_route_not_found(client, mock_reader):
    mock_reader.get_by_id.side_effect = NotFoundError("Estabelecimento não encontrado.")

    response = client.get(f"/establishments/{uuid.uuid7()}")

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_update_establishment_route_success(client, mock_updater, establishment):
    mock_updater.update.return_value = establishment

    response = client.patch(
        f"/establishments/{establishment.id}", json={"name": "Novo Nome"}
    )

    assert response.status_code == 200
    mock_updater.update.assert_awaited_once()


def test_delete_establishment_route_success(client, mock_deleter, establishment):
    response = client.delete(f"/establishments/{establishment.id}")

    assert response.status_code == 204
    mock_deleter.delete.assert_awaited_once_with(establishment.id)


def test_activate_establishment_route_success(client, mock_activator, establishment):
    mock_activator.activate.return_value = establishment

    response = client.post(f"/establishments/{establishment.id}/activate")

    assert response.status_code == 200
    mock_activator.activate.assert_awaited_once_with(establishment.id)


def test_deactivate_establishment_route_success(client, mock_activator, establishment):
    mock_activator.deactivate.return_value = establishment

    response = client.post(f"/establishments/{establishment.id}/deactivate")

    assert response.status_code == 200
    mock_activator.deactivate.assert_awaited_once_with(establishment.id)
