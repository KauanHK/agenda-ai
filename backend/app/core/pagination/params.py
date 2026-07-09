from dataclasses import dataclass


@dataclass(frozen=True)
class PageParams:
    page: int = 1
    page_size: int = 20


@dataclass(frozen=True)
class Page[T]:
    items: list[T]
    total: int
    page: int
    page_size: int
