"""Compat: o `SchedulingNotificationsCanceller` agora vive em
`app.modules.scheduling_notifications.application.use_cases.cancel`. Re-export para
imports antigos."""

from app.modules.scheduling_notifications.application.use_cases.cancel import (
    SchedulingNotificationsCanceller,
)

__all__ = ["SchedulingNotificationsCanceller"]
