"""Compat: os filtros agora vivem em
`app.modules.scheduling_notifications.application.dtos.filters`. Re-export para
imports antigos."""

from app.modules.scheduling_notifications.application.dtos.filters import (
    SchedulingNotificationFilters,
)

__all__ = ["SchedulingNotificationFilters"]
