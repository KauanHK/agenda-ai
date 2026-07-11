import uuid

from app.core.pagination.params import Page
from app.core.roles import UserRole
from app.modules.memberships.domain.entities import (
    MembershipExpanded,
    MembershipUser,
    MembershipWithUser,
)

ESTABLISHMENT_ID = uuid.uuid7()


def make_membership_user() -> MembershipUser:
    return MembershipUser(
        id=uuid.uuid7(),
        name="Usuario Teste",
        email="usuario@email.com",
        phone=None,
        is_active=True,
    )


def make_membership_with_user() -> MembershipWithUser:
    return MembershipWithUser(
        id=uuid.uuid7(),
        establishment_id=ESTABLISHMENT_ID,
        role=UserRole.MEMBER,
        is_active=True,
        user=make_membership_user(),
    )


def make_membership_expanded() -> MembershipExpanded:
    return MembershipExpanded(
        role=UserRole.MEMBER,
        is_active=True,
        user=make_membership_user(),
        establishment={
            "id": uuid.uuid7(),
            "name": "Estabelecimento Teste",
            "document": "11222333000181",
            "document_type": "cnpj",
            "is_active": True,
            "timezone": "America/Sao_Paulo",
            "street": "Rua A",
            "number": "1",
            "complement": "",
            "neighborhood": "Centro",
            "city": "São Paulo",
            "state": "SP",
            "zip_code": "01310100",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        },
    )


def test_list_members_route_success(client, mock_reader):
    membership = make_membership_with_user()
    mock_reader.paginate.return_value = Page(
        items=[membership], total=1, page=1, page_size=10
    )

    response = client.get(f"/establishments/{ESTABLISHMENT_ID}/members")

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["total"] == 1
    mock_reader.paginate.assert_awaited_once()


def test_add_member_existing_user_route_success(client, mock_creator):
    expanded = make_membership_expanded()
    mock_creator.create.return_value = expanded

    response = client.post(
        f"/establishments/{ESTABLISHMENT_ID}/members",
        json={"user_id": str(uuid.uuid7()), "role": "member"},
    )

    assert response.status_code == 201, response.text
    mock_creator.create.assert_awaited_once()


def test_add_member_new_user_route_success(client, mock_creator):
    expanded = make_membership_expanded()
    mock_creator.create.return_value = expanded

    response = client.post(
        f"/establishments/{ESTABLISHMENT_ID}/members",
        json={
            "name": "Novo Membro",
            "email": "novo@email.com",
            "password": "senha1234",
            "role": "member",
        },
    )

    assert response.status_code == 201, response.text
    mock_creator.create.assert_awaited_once()


def test_get_member_route_success(client, mock_reader):
    expanded = make_membership_expanded()
    mock_reader.get_by_user_and_establishment.return_value = expanded

    response = client.get(f"/establishments/{ESTABLISHMENT_ID}/members/{uuid.uuid7()}")

    assert response.status_code == 200, response.text
    mock_reader.get_by_user_and_establishment.assert_awaited_once()


def test_update_member_route_success(client, mock_updater):
    membership = make_membership_with_user()
    mock_updater.update.return_value = membership

    response = client.patch(
        f"/establishments/{ESTABLISHMENT_ID}/members/{uuid.uuid7()}",
        json={"role": "establishment_admin"},
    )

    assert response.status_code == 200, response.text
    mock_updater.update.assert_awaited_once()


def test_remove_member_route_success(client, mock_deleter):
    response = client.delete(f"/establishments/{ESTABLISHMENT_ID}/members/{uuid.uuid7()}")

    assert response.status_code == 204
    mock_deleter.delete.assert_awaited_once()


def test_activate_member_route_success(client, mock_activator):
    membership = make_membership_with_user()
    mock_activator.activate.return_value = membership

    response = client.post(
        f"/establishments/{ESTABLISHMENT_ID}/members/{uuid.uuid7()}/activate"
    )

    assert response.status_code == 200, response.text
    mock_activator.activate.assert_awaited_once()


def test_deactivate_member_route_success(client, mock_activator):
    membership = make_membership_with_user()
    mock_activator.deactivate.return_value = membership

    response = client.post(
        f"/establishments/{ESTABLISHMENT_ID}/members/{uuid.uuid7()}/deactivate"
    )

    assert response.status_code == 200, response.text
    mock_activator.deactivate.assert_awaited_once()


def test_list_user_memberships_route_success(client, mock_reader):
    membership = make_membership_with_user()
    mock_reader.list_by_user.return_value = [membership]

    response = client.get(f"/users/{uuid.uuid7()}/memberships")

    assert response.status_code == 200, response.text
    assert len(response.json()) == 1
    mock_reader.list_by_user.assert_awaited_once()
