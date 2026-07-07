import uuid

import pytest

from app.api.deps.auth import get_current_establishment_actor
from app.core.actors.user import Membership, UserActor
from app.core.exceptions import ForbiddenError


@pytest.fixture(autouse=True)
def mock_establishment_actor(app, establishment_id):
    actor = UserActor(
        user_id=uuid.uuid7(),
        is_global_admin=False,
        memberships=(Membership(establishment_id=establishment_id, role="member"),),
    )
    app.dependency_overrides[get_current_establishment_actor] = lambda: actor
    return actor


def test_get_operating_hours_success(client, mock_reader, hour_read, establishment_id):
    mock_reader.list.return_value = [hour_read]

    response = client.get(f"/establishments/{establishment_id}/operating-hours")

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 1
    assert body[0]["weekday"] == hour_read.weekday
    mock_reader.list.assert_awaited_once()


def test_get_operating_hours_empty(client, mock_reader, establishment_id):
    mock_reader.list.return_value = []

    response = client.get(f"/establishments/{establishment_id}/operating-hours")

    assert response.status_code == 200
    assert response.json() == []


def test_get_operating_hours_forbidden_for_global_admin(
    client, mock_reader, establishment_id
):
    mock_reader.list.side_effect = ForbiddenError(
        "global_admin não opera sobre horários de funcionamento."
    )

    response = client.get(f"/establishments/{establishment_id}/operating-hours")

    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"


def test_get_operating_hours_forbidden_when_not_member(
    client, mock_reader, establishment_id
):
    mock_reader.list.side_effect = ForbiddenError(
        "Acesso negado a este estabelecimento."
    )

    response = client.get(f"/establishments/{establishment_id}/operating-hours")

    assert response.status_code == 403


def test_get_operating_hours_invalid_uuid(client):
    response = client.get("/establishments/invalid-uuid/operating-hours")

    assert response.status_code == 422


def test_put_operating_hours_success(client, mock_updater, hour_read, establishment_id):
    mock_updater.update.return_value = [hour_read]

    payload = {
        "items": [
            {"weekday": 0, "start_time": "09:00:00", "end_time": "18:00:00"},
        ]
    }

    response = client.put(
        f"/establishments/{establishment_id}/operating-hours",
        json=payload,
    )

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    mock_updater.update.assert_awaited_once()


def test_put_operating_hours_forbidden_for_member(
    client, mock_updater, establishment_id
):
    mock_updater.update.side_effect = ForbiddenError(
        "Apenas establishment_admin pode editar horários de funcionamento."
    )

    payload = {
        "items": [{"weekday": 0, "start_time": "09:00:00", "end_time": "18:00:00"}]
    }

    response = client.put(
        f"/establishments/{establishment_id}/operating-hours",
        json=payload,
    )

    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"


def test_put_operating_hours_forbidden_for_global_admin(
    client, mock_updater, establishment_id
):
    mock_updater.update.side_effect = ForbiddenError(
        "global_admin não opera sobre horários de funcionamento."
    )

    payload = {
        "items": [{"weekday": 0, "start_time": "09:00:00", "end_time": "18:00:00"}]
    }

    response = client.put(
        f"/establishments/{establishment_id}/operating-hours",
        json=payload,
    )

    assert response.status_code == 403


def test_put_operating_hours_validation_invalid_weekday(client, establishment_id):
    payload = {
        "items": [{"weekday": 7, "start_time": "09:00:00", "end_time": "18:00:00"}]
    }

    response = client.put(
        f"/establishments/{establishment_id}/operating-hours",
        json=payload,
    )

    assert response.status_code == 422


def test_put_operating_hours_validation_negative_weekday(client, establishment_id):
    payload = {
        "items": [{"weekday": -1, "start_time": "09:00:00", "end_time": "18:00:00"}]
    }

    response = client.put(
        f"/establishments/{establishment_id}/operating-hours",
        json=payload,
    )

    assert response.status_code == 422


def test_put_operating_hours_validation_end_before_start(client, establishment_id):
    payload = {
        "items": [{"weekday": 0, "start_time": "18:00:00", "end_time": "09:00:00"}]
    }

    response = client.put(
        f"/establishments/{establishment_id}/operating-hours",
        json=payload,
    )

    assert response.status_code == 422


def test_put_operating_hours_validation_equal_times(client, establishment_id):
    payload = {
        "items": [{"weekday": 0, "start_time": "09:00:00", "end_time": "09:00:00"}]
    }

    response = client.put(
        f"/establishments/{establishment_id}/operating-hours",
        json=payload,
    )

    assert response.status_code == 422


def test_put_operating_hours_validation_duplicate_weekday(client, establishment_id):
    payload = {
        "items": [
            {"weekday": 0, "start_time": "09:00:00", "end_time": "18:00:00"},
            {"weekday": 0, "start_time": "10:00:00", "end_time": "19:00:00"},
        ]
    }

    response = client.put(
        f"/establishments/{establishment_id}/operating-hours",
        json=payload,
    )

    assert response.status_code == 200


def test_put_operating_hours_validation_missing_items(client, establishment_id):
    response = client.put(
        f"/establishments/{establishment_id}/operating-hours",
        json={},
    )

    assert response.status_code == 422
