"""Compat: as dependências HTTP agora vivem em
`app.modules.scheduling_notifications.adapters.http.dependencies`. Re-export para
imports antigos."""

from app.modules.scheduling_notifications.adapters.http.dependencies import (
    PaginationFiltersDep,
    SchedulingNotificationsUnitOfWorkDep,
    get_pagination_filters,
)

__all__ = [
    "PaginationFiltersDep",
    "SchedulingNotificationsUnitOfWorkDep",
    "get_pagination_filters",
]
