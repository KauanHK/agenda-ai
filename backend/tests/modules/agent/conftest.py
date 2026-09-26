"""Fixtures compartilhadas da suíte."""

import logging
from collections.abc import Iterator

import pytest


@pytest.fixture(autouse=True)
def _isolate_root_logging() -> Iterator[None]:
    """`configure_logging` (via `create_app`/`main`) mexe no root com `force=True`.

    Cada teste começa e termina com a config de logging que o pytest montou.
    """
    root = logging.getLogger()
    saved_handlers = root.handlers[:]
    saved_level = root.level
    quieted = [logging.getLogger(name) for name in ("httpx", "httpcore")]
    saved_quieted_levels = [logger.level for logger in quieted]
    try:
        yield
    finally:
        root.handlers[:] = saved_handlers
        root.setLevel(saved_level)
        for logger, level in zip(quieted, saved_quieted_levels, strict=True):
            logger.setLevel(level)
