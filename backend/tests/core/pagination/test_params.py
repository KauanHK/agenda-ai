from dataclasses import FrozenInstanceError

import pytest

from app.core.pagination.params import Page, PageParams


class TestPageParams:
    def test_default_page_is_1(self):
        params = PageParams()

        assert params.page == 1

    def test_default_page_size_is_20(self):
        params = PageParams()

        assert params.page_size == 20

    def test_accepts_custom_values(self):
        params = PageParams(page=3, page_size=50)

        assert params.page == 3
        assert params.page_size == 50

    def test_is_frozen(self):
        params = PageParams()

        with pytest.raises(FrozenInstanceError):
            params.page = 2  # type: ignore[misc]


class TestPage:
    def test_stores_fields(self):
        page = Page(items=[1, 2, 3], total=42, page=5, page_size=25)

        assert page.items == [1, 2, 3]
        assert page.total == 42
        assert page.page == 5
        assert page.page_size == 25

    def test_is_frozen(self):
        page = Page(items=[], total=0, page=1, page_size=10)

        with pytest.raises(FrozenInstanceError):
            page.page = 2  # type: ignore[misc]

    def test_accepts_typed_items(self):
        items = ["a", "b", "c"]
        page: Page[str] = Page(items=items, total=3, page=1, page_size=10)

        assert page.items == items
