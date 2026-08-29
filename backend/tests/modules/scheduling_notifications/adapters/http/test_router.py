import uuid

from app.core.exceptions import NotFoundError
from app.core.pagination.params import Page
from app.modules.scheduling_notifications.domain.enums import NotificationStatus
from tests.modules.scheduling_notifications.application.use_cases.conftest import (
    make_notification,
)


def base_url(establishment_id) -> str:
    return f"/establishments/{establishment_id}/notifications"


def test_list_notifications_route_success(client, notifications_repo, establishment_id):
    notification = make_notification(establishment_id)
    notifications_repo.paginate.return_value = Page(
        items=[notification], total=1, page=1, page_size=10
    )

    response = client.get(base_url(establishment_id), params={"page": 1, "size": 10})

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] == 1
    assert body["data"][0]["id"] == str(notification.id)


def test_get_notification_route_success(client, notifications_repo, establishment_id):
    notification = make_notification(establishment_id)
    notifications_repo.get_by_id.return_value = notification

    response = client.get(f"{base_url(establishment_id)}/{notification.id}")

    assert response.status_code == 200, response.text
    assert response.json()["id"] == str(notification.id)


def test_get_notification_route_not_found(client, notifications_repo, establishment_id):
    notifications_repo.get_by_id.side_effect = NotFoundError(
        "Notificação não encontrada."
    )

    response = client.get(f"{base_url(establishment_id)}/{uuid.uuid7()}")

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_cancel_notification_route_success(
    client, notifications_repo, establishment_id
):
    notification = make_notification(establishment_id)
    notifications_repo.get_by_id.return_value = notification
    notifications_repo.update.return_value = make_notification(
        establishment_id, status=NotificationStatus.cancelled
    )

    response = client.post(f"{base_url(establishment_id)}/{notification.id}/cancel")

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "cancelled"


def test_cancel_notification_route_rejects_non_pending(
    client, notifications_repo, establishment_id
):
    notifications_repo.get_by_id.return_value = make_notification(
        establishment_id, status=NotificationStatus.sent
    )

    response = client.post(f"{base_url(establishment_id)}/{uuid.uuid7()}/cancel")

    assert response.status_code == 422
