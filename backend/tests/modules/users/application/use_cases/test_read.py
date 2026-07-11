import pytest

from app.core.exceptions import ForbiddenError
from app.core.pagination.params import Page, PageParams
from app.modules.users.application.dtos.filters import UserFilters
from app.modules.users.application.use_cases.read import UsersReader
from app.modules.users.domain.entities import UserExpanded
from tests.modules.users.application.use_cases.conftest import (
    FakeUsersUnitOfWork,
    make_actor,
    make_user_expanded,
)


@pytest.fixture
def reader(uow: FakeUsersUnitOfWork) -> UsersReader:
    return UsersReader(uow=uow)


@pytest.fixture
def page_params() -> PageParams:
    return PageParams(page=1, page_size=10)


async def test_get_by_id_returns_user_expanded(reader, mock_repo, user):
    expanded = make_user_expanded()
    mock_repo.get_by_id_expanded.return_value = expanded
    actor = make_actor(is_global_admin=True)

    result = await reader.get_by_id(user.id, actor)

    assert isinstance(result, UserExpanded)
    assert result is expanded


async def test_get_by_id_calls_repository(reader, mock_repo, user):
    expanded = make_user_expanded()
    mock_repo.get_by_id_expanded.return_value = expanded
    actor = make_actor(is_global_admin=True)

    await reader.get_by_id(user.id, actor)

    mock_repo.get_by_id_expanded.assert_awaited_once_with(user.id)


async def test_get_by_id_allowed_for_non_global_admin(reader, mock_repo, user):
    expanded = make_user_expanded()
    mock_repo.get_by_id_expanded.return_value = expanded
    actor = make_actor(is_global_admin=False)

    result = await reader.get_by_id(user.id, actor)

    assert isinstance(result, UserExpanded)


async def test_paginate_returns_page(reader, mock_repo, user, page_params):
    page = Page(items=[user], total=1, page=1, page_size=10)
    mock_repo.paginate.return_value = page
    actor = make_actor(is_global_admin=True)

    result = await reader.paginate(page_params, actor)

    assert isinstance(result, Page)
    assert result.items == [user]
    assert result.total == 1


async def test_paginate_calls_repository(reader, mock_repo, page_params):
    mock_repo.paginate.return_value = Page(items=[], total=0, page=1, page_size=10)
    actor = make_actor(is_global_admin=True)

    await reader.paginate(page_params, actor)

    mock_repo.paginate.assert_awaited_once()


async def test_paginate_preserves_incoming_filters(reader, mock_repo, page_params):
    mock_repo.paginate.return_value = Page(items=[], total=0, page=1, page_size=10)
    actor = make_actor(is_global_admin=True)
    incoming_filters = UserFilters(q="teste", is_active=True)

    await reader.paginate(page_params, actor, filters=incoming_filters)

    filters = mock_repo.paginate.call_args.kwargs["filters"]
    assert filters.q == "teste"
    assert filters.is_active is True


async def test_paginate_raises_forbidden_for_non_global_admin(
    reader, mock_repo, page_params
):
    actor = make_actor(is_global_admin=False)

    with pytest.raises(ForbiddenError):
        await reader.paginate(page_params, actor)

    mock_repo.paginate.assert_not_awaited()
