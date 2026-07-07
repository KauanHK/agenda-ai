import uuid

import pytest

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.pagination import PaginatedResponse, PaginationParams
from app.modules.services.application.read import ServicesReader
from app.modules.services.domain.filters import ServiceFilters
from app.modules.services.domain.schemas import ServiceRead


@pytest.fixture
def reader(mock_uow) -> ServicesReader:
    return ServicesReader(uow=mock_uow)


@pytest.fixture
def pagination() -> PaginationParams:
    return PaginationParams(page=1, size=10)


async def test_get_by_id_returns_service_read_for_same_tenant(
    reader, admin_user, establishment_id, service_model
):
    result = await reader.get_by_id(service_model.id, admin_user, establishment_id)

    assert isinstance(result, ServiceRead)
    assert result.id == service_model.id


async def test_get_by_id_calls_repository(
    reader, mock_repo, admin_user, establishment_id, service_model
):
    await reader.get_by_id(service_model.id, admin_user, establishment_id)

    mock_repo.get_by_id.assert_awaited_once_with(service_model.id)


async def test_get_by_id_raises_not_found_for_other_tenant(
    reader, admin_user, establishment_id, service_model
):
    service_model.establishment_id = uuid.uuid7()

    with pytest.raises(NotFoundError, match="Acesso negado"):
        await reader.get_by_id(service_model.id, admin_user, establishment_id)


async def test_get_by_id_forbidden_for_global_admin(
    reader, global_admin_user, establishment_id, service_model
):
    with pytest.raises(ForbiddenError, match="global_admin"):
        await reader.get_by_id(service_model.id, global_admin_user, establishment_id)


async def test_get_by_id_allowed_for_member(
    reader, member_user, establishment_id, service_model
):
    result = await reader.get_by_id(service_model.id, member_user, establishment_id)

    assert isinstance(result, ServiceRead)


async def test_paginate_returns_paginated_response(
    reader, pagination, admin_user, establishment_id
):
    result = await reader.paginate(pagination, establishment_id)

    assert isinstance(result, PaginatedResponse)
    assert len(result.data) == 1
    assert result.total == 1


async def test_paginate_preserves_q_and_is_active(
    reader, mock_repo, pagination, establishment_id
):
    incoming = ServiceFilters(
        establishment_id=establishment_id,
        q="corte",
        is_active=True,
    )

    await reader.paginate(
        pagination=pagination,
        filters=incoming,
    )

    filters = mock_repo.list.call_args[1]["filters"]
    assert filters.q == "corte"
    assert filters.is_active is True
    assert filters.establishment_id == establishment_id


async def test_paginate_allowed_for_member(
    reader, pagination, member_user, establishment_id
):
    result = await reader.paginate(pagination, establishment_id)

    assert isinstance(result, PaginatedResponse)


async def test_paginate_returns_empty(
    reader, mock_repo, pagination, admin_user, establishment_id
):
    mock_repo.list.return_value = []
    mock_repo.count.return_value = 0

    result = await reader.paginate(pagination, establishment_id)

    assert result.data == []
    assert result.total == 0
