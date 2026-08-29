import pytest

from app.core.exceptions import ForbiddenError
from app.core.pagination.params import Page, PageParams
from app.modules.clients.application.dtos.filters import ClientFilters
from app.modules.clients.application.use_cases.paginator import ClientsPaginator


@pytest.fixture
def page_params() -> PageParams:
    return PageParams(page=1, page_size=10)


async def test_paginate_returns_page(
    uow, clients_repo, page_params, admin_user, establishment_id, client_entity
):
    clients_repo.paginate.return_value = Page(
        items=[client_entity], total=1, page=1, page_size=10
    )

    page = await ClientsPaginator(uow).paginate(
        page_params, admin_user, establishment_id
    )

    assert page.total == 1
    assert page.items == [client_entity]


async def test_paginate_scopes_filters_to_establishment(
    uow, clients_repo, page_params, admin_user, establishment_id
):
    clients_repo.paginate.return_value = Page(
        items=[], total=0, page=1, page_size=10
    )

    await ClientsPaginator(uow).paginate(page_params, admin_user, establishment_id)

    sent: ClientFilters = clients_repo.paginate.call_args.kwargs["filters"]
    assert sent.establishment_id == str(establishment_id)


async def test_paginate_preserves_q_and_is_active(
    uow, clients_repo, page_params, admin_user, establishment_id
):
    clients_repo.paginate.return_value = Page(
        items=[], total=0, page=1, page_size=10
    )

    await ClientsPaginator(uow).paginate(
        page_params,
        admin_user,
        establishment_id,
        filters=ClientFilters(q="joao", is_active=True),
    )

    sent: ClientFilters = clients_repo.paginate.call_args.kwargs["filters"]
    assert sent.q == "joao"
    assert sent.is_active is True
    assert sent.establishment_id == str(establishment_id)


async def test_paginate_allowed_for_member(
    uow, clients_repo, page_params, member_user, establishment_id
):
    clients_repo.paginate.return_value = Page(
        items=[], total=0, page=1, page_size=10
    )

    page = await ClientsPaginator(uow).paginate(
        page_params, member_user, establishment_id
    )

    assert page.total == 0


async def test_paginate_forbidden_for_global_admin(
    uow, page_params, global_admin_user, establishment_id
):
    with pytest.raises(ForbiddenError, match="global_admin"):
        await ClientsPaginator(uow).paginate(
            page_params, global_admin_user, establishment_id
        )
