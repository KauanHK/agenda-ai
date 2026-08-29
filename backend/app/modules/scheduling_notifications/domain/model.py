"""Compat: o model SQLAlchemy agora vive em
`app.modules.scheduling_notifications.adapters.db.models`. Re-export para imports
antigos (consumido por app.modules.schedulings, app.modules.agent e pelo worker
Celery)."""

from app.modules.scheduling_notifications.adapters.db.models import (
    SchedulingNotification,
)

__all__ = ["SchedulingNotification"]
