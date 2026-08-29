import uuid

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.pagination.params import Page


def test_list_unavailabilities_route_success(
    client, unavailabilities_repo, unavailability_entity, establishment_id
):
    unavailabilities_repo.paginate.return_value = Page(
        items=[unavailability_entity], total=1, page=1, page_size=10
    )

    response = client.get(
        f"/establishments/{establishment_id}/unavailabilities",
        params={"page": 1, "size": 10},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] == 1
    assert len(body["data"]) == 1
    assert body["data"][0]["id"] == str(unavailability_entity.id)
    assert body["page"] == 1
    assert body["size"] == 10


def test_get_unavailability_route_success(
    client, unavailabilities_repo, unavailability_entity, establishment_id
):
    unavailabilities_repo.get_by_id.return_value = unavailability_entity

    response = client.get(
        f"/establishments/{establishment_id}/unavailabilities/{unavailability_entity.id}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(unavailability_entity.id)
    assert response.json()["reason"] == "Feriado"


def test_get_unavailability_route_not_found(
    client, unavailabilities_repo, establishment_id
):
    unavailabilities_repo.get_by_id.side_effect = NotFoundError(
        "Unavailability não encontrada."
    )

    response = client.get(
        f"/establishments/{establishment_id}/unavailabilities/{uuid.uuid7()}"
    )

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_create_unavailability_route_success(
    client, unavailabilities_repo, unavailability_entity, establishment_id
):
    unavailabilities_repo.create.return_value = unavailability_entity

    payload = {
        "starts_at": unavailability_entity.starts_at.isoformat(),
        "ends_at": unavailability_entity.ends_at.isoformat(),
        "reason": "Feriado",
    }

    response = client.post(
        f"/establishments/{establishment_id}/unavailabilities", json=payload
    )

    assert response.status_code == 201, response.text
    assert response.json()["reason"] == "Feriado"
    unavailabilities_repo.create.assert_awaited_once()


def test_create_unavailability_route_forbidden_for_member(
    client, unavailabilities_repo, unavailability_entity, establishment_id
):
    unavailabilities_repo.create.side_effect = ForbiddenError(
        "Apenas establishment_admin pode escrever unavailabilities."
    )

    payload = {
        "starts_at": unavailability_entity.starts_at.isoformat(),
        "ends_at": unavailability_entity.ends_at.isoformat(),
    }

    response = client.post(
        f"/establishments/{establishment_id}/unavailabilities", json=payload
    )

    assert response.status_code == 403


def test_update_unavailability_route_success(
    client, unavailabilities_repo, unavailability_entity, establishment_id
):
    unavailabilities_repo.get_by_id.return_value = unavailability_entity
    unavailabilities_repo.update.return_value = unavailability_entity

    response = client.patch(
        f"/establishments/{establishment_id}/unavailabilities/{unavailability_entity.id}",
        json={"reason": "Novo motivo"},
    )

    assert response.status_code == 200
    unavailabilities_repo.update.assert_awaited_once()


def test_delete_unavailability_route_success(
    client, unavailabilities_repo, unavailability_entity, establishment_id
):
    unavailabilities_repo.get_by_id.return_value = unavailability_entity

    response = client.delete(
        f"/establishments/{establishment_id}/unavailabilities/{unavailability_entity.id}"
    )

    assert response.status_code == 204
    unavailabilities_repo.delete.assert_awaited_once_with(unavailability_entity.id)
