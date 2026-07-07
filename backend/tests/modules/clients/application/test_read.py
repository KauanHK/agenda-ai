import uuid

import pytest

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.pagination import PaginatedResponse, PaginationParams
from app.modules.clients.application.read import ClientsReader
from app.modules.clients.domain.filters import ClientFilters
from app.modules.clients.domain.schemas import ClientRead


@pytest.fixture
def reader(mock_uow) -> ClientsReader:
    return ClientsReader(uow=mock_uow)


@pytest.fixture
def pagination() -> PaginationParams:
    return PaginationParams(page=1, size=10)


async def test_get_by_id_returns_client_read_for_same_tenant(
    reader, admin_user, establishment_id, client_model
):
    result = await reader.get_by_id(client_model.id, admin_user, establishment_id)

    assert isinstance(result, ClientRead)
    assert result.id == client_model.id


async def test_get_by_id_calls_repository(
    reader, mock_repo, admin_user, establishment_id, client_model
):
    await reader.get_by_id(client_model.id, admin_user, establishment_id)

    mock_repo.get_by_id.assert_awaited_once_with(client_model.id)


async def test_get_by_id_raises_not_found_for_other_tenant(
    reader, admin_user, establishment_id, client_model
):
    client_model.establishment_id = uuid.uuid7()

    with pytest.raises(NotFoundError, match="Acesso negado"):
        await reader.get_by_id(client_model.id, admin_user, establishment_id)


async def test_get_by_id_forbidden_for_global_admin(
    reader, global_admin_user, establishment_id, client_model
):
    with pytest.raises(ForbiddenError, match="global_admin"):
        await reader.get_by_id(client_model.id, global_admin_user, establishment_id)


async def test_get_by_id_allowed_for_member(
    reader, member_user, establishment_id, client_model
):
    result = await reader.get_by_id(client_model.id, member_user, establishment_id)

    assert isinstance(result, ClientRead)


async def test_paginate_returns_paginated_response(
    reader, pagination, admin_user, establishment_id
):
    result = await reader.paginate(pagination, admin_user, establishment_id)

    assert isinstance(result, PaginatedResponse)
    assert len(result.data) == 1
    assert result.total == 1


async def test_paginate_scopes_to_establishment(
    reader, mock_repo, pagination, admin_user, establishment_id
):
    await reader.paginate(pagination, admin_user, establishment_id)

    filters = mock_repo.list.call_args[1]["filters"]
    assert filters.establishment_id == str(establishment_id)


async def test_paginate_preserves_q_and_is_active(
    reader, mock_repo, pagination, admin_user, establishment_id
):
    incoming = ClientFilters(q="joao", is_active=True)

    await reader.paginate(pagination, admin_user, establishment_id, filters=incoming)

    filters = mock_repo.list.call_args[1]["filters"]
    assert filters.q == "joao"
    assert filters.is_active is True
    assert filters.establishment_id == str(establishment_id)


async def test_paginate_forbidden_for_global_admin(
    reader, pagination, global_admin_user, establishment_id
):
    with pytest.raises(ForbiddenError, match="global_admin"):
        await reader.paginate(pagination, global_admin_user, establishment_id)


async def test_paginate_allowed_for_member(
    reader, pagination, member_user, establishment_id
):
    result = await reader.paginate(pagination, member_user, establishment_id)

    assert isinstance(result, PaginatedResponse)


async def test_paginate_returns_empty(
    reader, mock_repo, pagination, admin_user, establishment_id
):
    mock_repo.list.return_value = []
    mock_repo.count.return_value = 0

    result = await reader.paginate(pagination, admin_user, establishment_id)

    assert result.data == []
    assert result.total == 0
