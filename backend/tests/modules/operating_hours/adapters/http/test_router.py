from app.core.exceptions import ForbiddenError
from tests.modules.operating_hours.application.use_cases.conftest import (
    make_operating_hour,
)


def base_url(establishment_id) -> str:
    return f"/establishments/{establishment_id}/operating-hours"


def test_get_operating_hours_route_success(
    client, operating_hours_repo, establishment_id
):
    hour = make_operating_hour(establishment_id)
    operating_hours_repo.list_by_establishment.return_value = [hour]

    response = client.get(base_url(establishment_id))

    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == str(hour.id)
    assert body[0]["weekday"] == hour.weekday


def test_update_operating_hours_route_success(
    client, operating_hours_repo, establishment_id
):
    hour = make_operating_hour(establishment_id)
    operating_hours_repo.replace_all.return_value = [hour]

    payload = {
        "items": [
            {"weekday": 1, "start_time": "08:00:00", "end_time": "18:00:00"},
        ]
    }

    response = client.put(base_url(establishment_id), json=payload)

    assert response.status_code == 200, response.text
    operating_hours_repo.replace_all.assert_awaited_once()


def test_update_operating_hours_route_validation_error(client, establishment_id):
    payload = {
        "items": [
            {"weekday": 1, "start_time": "18:00:00", "end_time": "08:00:00"},
        ]
    }

    response = client.put(base_url(establishment_id), json=payload)

    assert response.status_code == 422


def test_update_operating_hours_route_forbidden(
    client, operating_hours_repo, establishment_id
):
    operating_hours_repo.replace_all.side_effect = ForbiddenError(
        "Apenas establishment_admin pode editar horários de funcionamento."
    )

    payload = {
        "items": [
            {"weekday": 1, "start_time": "08:00:00", "end_time": "18:00:00"},
        ]
    }

    response = client.put(base_url(establishment_id), json=payload)

    assert response.status_code == 403
