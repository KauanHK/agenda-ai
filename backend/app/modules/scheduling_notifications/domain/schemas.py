"""Compat: os schemas HTTP agora vivem em
`app.modules.scheduling_notifications.adapters.http.schemas`. Re-export para imports
antigos."""

from app.modules.scheduling_notifications.adapters.http.schemas import (
    SchedulingNotificationRead,
)

__all__ = ["SchedulingNotificationRead"]
