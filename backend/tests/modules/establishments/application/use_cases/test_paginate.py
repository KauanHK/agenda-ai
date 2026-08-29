from app.core.pagination.params import Page, PageParams
from app.modules.establishments.application.dtos.filters import EstablishmentFilters
from app.modules.establishments.application.use_cases.paginator import (
    EstablishmentsPaginator,
)


async def test_paginate_returns_page(uow, establishments_repo, establishment):
    establishments_repo.paginate.return_value = Page(
        items=[establishment], total=1, page=1, page_size=10
    )

    page = await EstablishmentsPaginator(uow).paginate(PageParams(page=1, page_size=10))

    assert page.total == 1
    assert page.items == [establishment]


async def test_paginate_passes_filters(uow, establishments_repo, establishment):
    establishments_repo.paginate.return_value = Page(
        items=[], total=0, page=1, page_size=10
    )
    filters = EstablishmentFilters(name="Clínica", document="11222333000181")

    await EstablishmentsPaginator(uow).paginate(
        PageParams(page=1, page_size=10), filters=filters
    )

    establishments_repo.paginate.assert_awaited_once()
    assert establishments_repo.paginate.call_args.kwargs["filters"] == filters
