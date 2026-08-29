import uuid

from app.core.exceptions import NotFoundError
from app.core.pagination.params import Page


def base_url(establishment_id) -> str:
    return f"/establishments/{establishment_id}/messaging-templates"


def test_list_messaging_templates_route_success(
    client, templates_repo, template_entity, establishment_id
):
    templates_repo.paginate.return_value = Page(
        items=[template_entity], total=1, page=1, page_size=10
    )

    response = client.get(base_url(establishment_id), params={"page": 1, "size": 10})

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] == 1
    assert body["data"][0]["id"] == str(template_entity.id)


def test_get_messaging_template_route_success(
    client, templates_repo, template_entity, establishment_id
):
    templates_repo.get_by_id.return_value = template_entity
    templates_repo.list_services_for_template.return_value = []

    response = client.get(f"{base_url(establishment_id)}/{template_entity.id}")

    assert response.status_code == 200, response.text
    assert response.json()["id"] == str(template_entity.id)
    assert response.json()["services"] == []


def test_get_messaging_template_route_not_found(
    client, templates_repo, establishment_id
):
    templates_repo.get_by_id.side_effect = NotFoundError("Template não encontrado.")

    response = client.get(f"{base_url(establishment_id)}/{uuid.uuid7()}")

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_create_messaging_template_route_success(
    client, templates_repo, template_entity, establishment_id
):
    templates_repo.create.return_value = template_entity

    payload = {
        "name": "Lembrete padrão",
        "content": "Olá {cliente}!",
        "type": "reminder",
        "minutes_before": 60,
    }

    response = client.post(base_url(establishment_id), json=payload)

    assert response.status_code == 201, response.text
    assert response.json()["name"] == template_entity.name
    templates_repo.create.assert_awaited_once()


def test_create_messaging_template_route_validation_error(client, establishment_id):
    response = client.post(base_url(establishment_id), json={"name": "", "content": ""})

    assert response.status_code == 422


def test_update_messaging_template_route_success(
    client, templates_repo, template_entity, establishment_id
):
    templates_repo.get_by_id.return_value = template_entity
    templates_repo.update.return_value = template_entity

    response = client.patch(
        f"{base_url(establishment_id)}/{template_entity.id}",
        json={"name": "Novo nome"},
    )

    assert response.status_code == 200, response.text
    templates_repo.update.assert_awaited_once()


def test_delete_messaging_template_route_success(
    client, templates_repo, template_entity, establishment_id
):
    templates_repo.get_by_id.return_value = template_entity

    response = client.delete(f"{base_url(establishment_id)}/{template_entity.id}")

    assert response.status_code == 204, response.text
    templates_repo.update.assert_awaited_once()
