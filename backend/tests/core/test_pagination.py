import pytest
from pydantic import ValidationError

from app.core.pagination import (
    PaginatedResponse,
    PaginationParams,
    build_paginated_response,
)


def test_pagination_params_defaults():
    params = PaginationParams()
    assert params.page == 1
    assert params.size == 10


def test_pagination_params_offset_first_page():
    params = PaginationParams(page=1, size=10)
    assert params.offset == 0


def test_pagination_params_offset_second_page():
    params = PaginationParams(page=2, size=10)
    assert params.offset == 10


def test_pagination_params_offset_custom_size():
    params = PaginationParams(page=3, size=25)
    assert params.offset == 50


def test_pagination_params_invalid_page():
    with pytest.raises(ValidationError):
        PaginationParams(page=0)


def test_pagination_params_invalid_size_zero():
    with pytest.raises(ValidationError):
        PaginationParams(size=0)


def test_pagination_params_invalid_size_above_limit():
    with pytest.raises(ValidationError):
        PaginationParams(size=101)


def test_total_pages_exact_division():
    response = PaginatedResponse(data=[], total=20, page=1, size=10)
    assert response.total_pages == 2


def test_total_pages_with_remainder():
    response = PaginatedResponse(data=[], total=21, page=1, size=10)
    assert response.total_pages == 3


def test_total_pages_single_page():
    response = PaginatedResponse(data=[], total=5, page=1, size=10)
    assert response.total_pages == 1


def test_total_pages_when_total_is_zero():
    response = PaginatedResponse(data=[], total=0, page=1, size=10)
    assert response.total_pages == 0


def test_total_pages_total_equals_size():
    response = PaginatedResponse(data=[], total=10, page=1, size=10)
    assert response.total_pages == 1


def test_build_paginated_response_structure():
    params = PaginationParams(page=2, size=5)
    items = [1, 2, 3, 4, 5]
    response = build_paginated_response(items=items, total=20, params=params)

    assert response.data == items
    assert response.total == 20
    assert response.page == 2
    assert response.size == 5


def test_build_paginated_response_empty_items():
    params = PaginationParams(page=1, size=10)
    response = build_paginated_response(items=[], total=0, params=params)

    assert response.data == []
    assert response.total == 0
    assert response.total_pages == 0


def test_build_paginated_response_converts_sequence_to_list():
    params = PaginationParams(page=1, size=10)
    response = build_paginated_response(items=(1, 2, 3), total=3, params=params)

    assert isinstance(response.data, list)
    assert response.data == [1, 2, 3]


def test_build_paginated_response_total_pages_computed():
    params = PaginationParams(page=1, size=10)
    response = build_paginated_response(items=[], total=25, params=params)

    assert response.total_pages == 3
