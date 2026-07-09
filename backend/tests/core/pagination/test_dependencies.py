from app.core.pagination.dependencies import get_pagination_params
from app.core.pagination.params import PageParams
from app.core.pagination.schemas import PaginationParams


def _make_query_params(page: int = 1, size: int = 10) -> PaginationParams:
    return PaginationParams(page=page, size=size)


class TestGetPaginationParams:
    def test_returns_page_params_instance(self):
        result = get_pagination_params(_make_query_params())

        assert isinstance(result, PageParams)

    def test_page_is_passed_correctly(self):
        result = get_pagination_params(_make_query_params(page=3))

        assert result.page == 3

    def test_size_is_mapped_to_page_size(self):
        result = get_pagination_params(_make_query_params(size=50))

        assert result.page_size == 50

    def test_passes_both_fields_correctly(self):
        result = get_pagination_params(_make_query_params(page=2, size=25))

        assert result.page == 2
        assert result.page_size == 25

    def test_default_values_are_forwarded(self):
        result = get_pagination_params(_make_query_params())

        assert result.page == 1
        assert result.page_size == 10
