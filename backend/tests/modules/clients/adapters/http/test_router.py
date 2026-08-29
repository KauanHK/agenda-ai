import dataclasses
import uuid

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.core.pagination.params import Page


def test_list_clients_route_success(
    client, clients_repo, client_entity, establishment_id
):
    clients_repo.paginate.return_value = Page(
        items=[client_entity], total=1, page=1, page_size=10
    )

    response = client.get(
        f"/establishments/{establishment_id}/clients",
        params={"page": 1, "size": 10, "q": "cli", "is_active": "true"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] == 1
    assert body["data"][0]["name"] == client_entity.name
    clients_repo.paginate.assert_awaited_once()


def test_get_client_route_success(
    client, clients_repo, client_entity, establishment_id
):
    clients_repo.get_by_id.return_value = client_entity

    response = client.get(
        f"/establishments/{establishment_id}/clients/{client_entity.id}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(client_entity.id)


def test_get_client_route_not_found(client, clients_repo, establishment_id):
    clients_repo.get_by_id.side_effect = NotFoundError("Acesso negado.")

    response = client.get(
        f"/establishments/{establishment_id}/clients/{uuid.uuid7()}"
    )

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_get_client_route_invalid_uuid(client, establishment_id):
    response = client.get(
        f"/establishments/{establishment_id}/clients/nao-e-uuid"
    )

    assert response.status_code == 422


def test_create_client_route_success(
    client, clients_repo, client_entity, establishment_id
):
    clients_repo.create.return_value = client_entity

    response = client.post(
        f"/establishments/{establishment_id}/clients",
        json={"name": "Novo", "phone": "11999998888", "email": "n@e.com"},
    )

    assert response.status_code == 201, response.text
    assert response.json()["name"] == client_entity.name
    clients_repo.create.assert_awaited_once()


def test_create_client_route_without_email(
    client, clients_repo, client_entity, establishment_id
):
    clients_repo.create.return_value = dataclasses.replace(client_entity, email=None)

    response = client.post(
        f"/establishments/{establishment_id}/clients",
        json={"name": "Sem Email", "phone": "11999998888"},
    )

    assert response.status_code == 201
    assert response.json()["email"] is None


def test_create_client_route_validation_error_missing_phone(client, establishment_id):
    response = client.post(
        f"/establishments/{establishment_id}/clients",
        json={"name": "Cliente"},
    )

    assert response.status_code == 422


def test_create_client_route_validation_error_invalid_email(client, establishment_id):
    response = client.post(
        f"/establishments/{establishment_id}/clients",
        json={"name": "Cliente", "phone": "11999990000", "email": "nope"},
    )

    assert response.status_code == 422


def test_create_client_route_conflict(client, clients_repo, establishment_id):
    clients_repo.create.side_effect = ConflictError(
        "Telefone ou e-mail já cadastrado neste estabelecimento."
    )

    response = client.post(
        f"/establishments/{establishment_id}/clients",
        json={"name": "Cliente", "phone": "11999990000"},
    )

    assert response.status_code == 409
    assert response.json()["code"] == "conflict"


def test_update_client_route_success(
    client, clients_repo, client_entity, establishment_id
):
    clients_repo.get_by_id.return_value = client_entity
    clients_repo.update.return_value = client_entity

    response = client.patch(
        f"/establishments/{establishment_id}/clients/{client_entity.id}",
        json={"name": "Novo Nome"},
    )

    assert response.status_code == 200
    clients_repo.update.assert_awaited_once()


def test_update_client_route_not_found(client, clients_repo, establishment_id):
    clients_repo.get_by_id.side_effect = NotFoundError("Acesso negado.")

    response = client.patch(
        f"/establishments/{establishment_id}/clients/{uuid.uuid7()}",
        json={"name": "Novo Nome"},
    )

    assert response.status_code == 404


def test_delete_client_route_success(
    client, clients_repo, client_entity, establishment_id
):
    clients_repo.get_by_id.return_value = client_entity

    response = client.delete(
        f"/establishments/{establishment_id}/clients/{client_entity.id}"
    )

    assert response.status_code == 204
    clients_repo.update.assert_awaited_once()


def test_activate_client_route_success(
    client, clients_repo, client_entity, establishment_id
):
    clients_repo.get_by_id.return_value = client_entity
    clients_repo.update.return_value = client_entity

    response = client.post(
        f"/establishments/{establishment_id}/clients/{client_entity.id}/activate"
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(client_entity.id)


def test_deactivate_client_route_success(
    client, clients_repo, client_entity, establishment_id
):
    clients_repo.get_by_id.return_value = client_entity
    clients_repo.update.return_value = client_entity

    response = client.post(
        f"/establishments/{establishment_id}/clients/{client_entity.id}/deactivate"
    )

    assert response.status_code == 200


def test_write_route_forbidden_is_mapped_to_403(
    client, clients_repo, establishment_id
):
    clients_repo.create.side_effect = ForbiddenError(
        "Apenas establishment_admin pode escrever clientes."
    )

    response = client.post(
        f"/establishments/{establishment_id}/clients",
        json={"name": "Cliente", "phone": "11999990000"},
    )

    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"
