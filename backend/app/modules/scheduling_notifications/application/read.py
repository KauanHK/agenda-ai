"""Compat: o `SchedulingNotificationsReader` agora vive em
`app.modules.scheduling_notifications.application.use_cases.read`. Re-export para
imports antigos."""

from app.modules.scheduling_notifications.application.use_cases.read import (
    SchedulingNotificationsReader,
)

__all__ = ["SchedulingNotificationsReader"]
