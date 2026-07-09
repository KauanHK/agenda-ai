from app.core.pagination.params import Page
from app.core.pagination.schemas import (
    PaginatedResponse,
    build_paginated_response_from_page,
)


class TestBuildPaginatedResponseFromPage:
    def test_returns_paginated_response(self):
        page = Page(items=[], total=0, page=1, page_size=10)

        result = build_paginated_response_from_page(page)

        assert isinstance(result, PaginatedResponse)

    def test_maps_items_to_data(self):
        page = Page(items=["a", "b"], total=2, page=1, page_size=10)

        result = build_paginated_response_from_page(page)

        assert result.data == ["a", "b"]

    def test_maps_page_size_to_size(self):
        page = Page(items=[], total=0, page=1, page_size=25)

        result = build_paginated_response_from_page(page)

        assert result.size == 25

    def test_maps_total_and_page(self):
        page = Page(items=[], total=99, page=4, page_size=10)

        result = build_paginated_response_from_page(page)

        assert result.total == 99
        assert result.page == 4

    def test_total_pages_is_computed(self):
        page = Page(items=[], total=15, page=1, page_size=10)

        result = build_paginated_response_from_page(page)

        assert result.total_pages == 2

    def test_json_contract_is_preserved(self):
        page = Page(items=[1], total=1, page=1, page_size=10)

        result = build_paginated_response_from_page(page)

        assert result.model_dump() == {
            "data": [1],
            "total": 1,
            "page": 1,
            "size": 10,
            "total_pages": 1,
        }
