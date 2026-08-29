"""Compat: `SchedulingNotificationsCreator` agora vive em
`app.modules.scheduling_notifications.application.use_cases.create`. Re-export para
imports antigos (consumido por app.modules.schedulings, app.modules.agent e pelo
worker Celery)."""

from app.modules.scheduling_notifications.application.use_cases.create import (
    SchedulingNotificationsCreator,
)

__all__ = ["SchedulingNotificationsCreator"]
